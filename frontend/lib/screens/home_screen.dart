/*
 * CipherMind home screen — cyberpunk dark theme with animated dot grid,
 * shimmer button, and glowing input field.
 */

import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/api_client.dart';
import '../core/constants.dart';
import 'analysis_screen.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

// ── Design tokens ─────────────────────────────────────────────────────────────
const _bg       = Color(0xFF06080F);
const _surface  = Color(0xFF0D1018);
const _card     = Color(0xFF131622);
const _purple   = Color(0xFF7C3AED);
const _cyan     = Color(0xFF06B6D4);
const _text     = Color(0xFFF1F5F9);
const _subtext  = Color(0xFF64748B);
const _errorColor = Color(0xFFF87171);

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});
  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen>
    with TickerProviderStateMixin {
  final TextEditingController _controller = TextEditingController();
  bool _isSubmitting = false;
  String? _error;
  bool _focused = false;

  late AnimationController _bgController;    // slow grid pulse
  late AnimationController _shimmerController; // button shimmer
  late AnimationController _entryController;  // initial load

  late Animation<double> _lockScale;
  late Animation<double> _titleFade;
  late Animation<Offset> _titleSlide;
  late Animation<double> _cardFade;
  late Animation<double> _shimmer;

  @override
  void initState() {
    super.initState();

    _bgController = AnimationController(vsync: this, duration: const Duration(seconds: 6))
      ..repeat();

    _shimmerController = AnimationController(vsync: this, duration: const Duration(milliseconds: 1600))
      ..repeat();
    _shimmer = Tween<double>(begin: -1.5, end: 2.5).animate(
      CurvedAnimation(parent: _shimmerController, curve: Curves.easeInOut),
    );

    _entryController = AnimationController(vsync: this, duration: const Duration(milliseconds: 900));
    _lockScale = Tween<double>(begin: 0.5, end: 1.0).animate(
      CurvedAnimation(parent: _entryController, curve: const Interval(0.0, 0.5, curve: Curves.elasticOut)),
    );
    _titleFade = CurvedAnimation(parent: _entryController, curve: const Interval(0.3, 0.7, curve: Curves.easeOut));
    _titleSlide = Tween<Offset>(begin: const Offset(0, 0.4), end: Offset.zero).animate(
      CurvedAnimation(parent: _entryController, curve: const Interval(0.3, 0.8, curve: Curves.easeOutCubic)),
    );
    _cardFade = CurvedAnimation(parent: _entryController, curve: const Interval(0.55, 1.0, curve: Curves.easeOut));

    _entryController.forward();
  }

  @override
  void dispose() {
    _bgController.dispose();
    _shimmerController.dispose();
    _entryController.dispose();
    _controller.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final text = _controller.text.trim();
    if (text.isEmpty) { setState(() => _error = 'Enter a ciphertext first.'); return; }
    if (text.length > AppConstants.maxCiphertextLength) {
      setState(() => _error = 'Input too long (max ${AppConstants.maxCiphertextLength} chars).');
      return;
    }
    setState(() { _isSubmitting = true; _error = null; });
    try {
      final api = ref.read(apiClientProvider);
      final resultData = await api.playground(text);
      if (!mounted) return;
      Navigator.push(context, _fadeRoute(AnalysisScreen(inlineResult: resultData)));
    } catch (e) {
      setState(() => _error = 'Failed: ${e.toString().replaceAll('DioException', '').trim()}');
    } finally {
      setState(() => _isSubmitting = false);
    }
  }

  Route _fadeRoute(Widget page) => PageRouteBuilder(
    pageBuilder: (_, a, __) => page,
    transitionsBuilder: (_, a, __, child) => FadeTransition(opacity: a, child: child),
    transitionDuration: const Duration(milliseconds: 400),
  );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      body: Stack(
        children: [
          // Animated grid background
          Positioned.fill(
            child: AnimatedBuilder(
              animation: _bgController,
              builder: (_, __) => CustomPaint(
                painter: DotGridPainter(_bgController.value),
              ),
            ),
          ),

          SafeArea(
            child: SingleChildScrollView(
              physics: const BouncingScrollPhysics(),
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  const SizedBox(height: 48),

                  // Lock icon with glow
                  ScaleTransition(
                    scale: _lockScale,
                    child: Container(
                      width: 80, height: 80,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: _purple.withOpacity(0.12),
                        boxShadow: [BoxShadow(color: _purple.withOpacity(0.35), blurRadius: 32, spreadRadius: 4)],
                        border: Border.all(color: _purple.withOpacity(0.5), width: 1.5),
                      ),
                      child: const Icon(Icons.lock_outline, color: _purple, size: 36),
                    ),
                  ),

                  const SizedBox(height: 20),

                  // Title
                  SlideTransition(
                    position: _titleSlide,
                    child: FadeTransition(
                      opacity: _titleFade,
                      child: Column(
                        children: [
                          ShaderMask(
                            shaderCallback: (r) => const LinearGradient(
                              colors: [_purple, _cyan],
                              begin: Alignment.centerLeft,
                              end: Alignment.centerRight,
                            ).createShader(r),
                            child: const Text(
                              'CIPHERMIND',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 30,
                                fontWeight: FontWeight.w900,
                                letterSpacing: 4,
                              ),
                            ),
                          ),
                          const SizedBox(height: 6),
                          const Text(
                            'Autonomous Cryptanalysis Engine',
                            style: TextStyle(color: _subtext, fontSize: 13, letterSpacing: 0.5),
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 40),

                  // Input card
                  FadeTransition(
                    opacity: _cardFade,
                    child: Focus(
                      onFocusChange: (v) => setState(() => _focused = v),
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 250),
                        decoration: BoxDecoration(
                          color: _card,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(
                            color: _focused
                                ? _purple.withOpacity(0.7)
                                : const Color(0xFF1E2130),
                            width: _focused ? 1.5 : 1,
                          ),
                          boxShadow: _focused
                              ? [BoxShadow(color: _purple.withOpacity(0.15), blurRadius: 24, spreadRadius: 2)]
                              : [],
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Padding(
                              padding: const EdgeInsets.fromLTRB(16, 14, 16, 0),
                              child: Row(
                                children: [
                                  Icon(Icons.terminal, color: _focused ? _purple : _subtext, size: 15),
                                  const SizedBox(width: 8),
                                  Text(
                                    'CIPHERTEXT INPUT',
                                    style: TextStyle(
                                      color: _focused ? _purple : _subtext,
                                      fontSize: 10,
                                      fontWeight: FontWeight.w700,
                                      letterSpacing: 1.5,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            TextField(
                              controller: _controller,
                              maxLines: 7,
                              maxLength: AppConstants.maxCiphertextLength,
                              style: const TextStyle(
                                fontFamily: 'monospace',
                                color: _text,
                                fontSize: 13,
                                height: 1.7,
                              ),
                              decoration: InputDecoration(
                                hintText: 'Paste any cipher — Caesar, Vigenère, Base64, Morse, Hex…',
                                hintStyle: TextStyle(color: _subtext.withOpacity(0.6), fontSize: 12),
                                contentPadding: const EdgeInsets.fromLTRB(16, 10, 16, 16),
                                border: InputBorder.none,
                                enabledBorder: InputBorder.none,
                                focusedBorder: InputBorder.none,
                                counterStyle: const TextStyle(color: _subtext, fontSize: 10),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),

                  if (_error != null) ...[
                    const SizedBox(height: 10),
                    FadeTransition(
                      opacity: _cardFade,
                      child: Row(
                        children: [
                          const Icon(Icons.error_outline, color: _errorColor, size: 14),
                          const SizedBox(width: 6),
                          Text(_error!, style: const TextStyle(color: _errorColor, fontSize: 12)),
                        ],
                      ),
                    ),
                  ],

                  const SizedBox(height: 20),

                  // Decode button
                  FadeTransition(
                    opacity: _cardFade,
                    child: SizedBox(
                      width: double.infinity,
                      height: 54,
                      child: _isSubmitting
                          ? _LoadingButton()
                          : _ShimmerButton(shimmer: _shimmer, onTap: _submit),
                    ),
                  ),

                  const SizedBox(height: 44),

                  // Example chips
                  FadeTransition(
                    opacity: _cardFade,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'TRY AN EXAMPLE',
                          style: TextStyle(color: _subtext, fontSize: 10, letterSpacing: 1.5, fontWeight: FontWeight.w700),
                        ),
                        const SizedBox(height: 12),
                        Wrap(
                          spacing: 8, runSpacing: 8,
                          children: [
                            _ExampleChip(label: 'Caesar ROT-3', text: 'KHOOR ZRUOG — WKH TXLFN EURZQ IRA', onTap: (t) => setState(() => _controller.text = t)),
                            _ExampleChip(label: 'Base64', text: 'SGVsbG8sIFdvcmxkIQ==', onTap: (t) => setState(() => _controller.text = t)),
                            _ExampleChip(label: 'Morse', text: '.... . .-.. .-.. --- / .-- --- .-. .-.. -..', onTap: (t) => setState(() => _controller.text = t)),
                            _ExampleChip(label: 'Hex', text: '48656c6c6f2c20576f726c6421', onTap: (t) => setState(() => _controller.text = t)),
                          ],
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 48),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Shimmer decode button ─────────────────────────────────────────────────────

class _ShimmerButton extends StatelessWidget {
  final Animation<double> shimmer;
  final VoidCallback onTap;
  const _ShimmerButton({required this.shimmer, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedBuilder(
        animation: shimmer,
        builder: (_, __) => Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            gradient: const LinearGradient(
              colors: [_purple, Color(0xFF5B21B6), _cyan],
              begin: Alignment.centerLeft,
              end: Alignment.centerRight,
            ),
            boxShadow: [
              BoxShadow(color: _purple.withOpacity(0.4), blurRadius: 20, offset: const Offset(0, 6)),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(14),
            child: Stack(
              children: [
                // Shimmer layer
                Positioned.fill(
                  child: Transform.translate(
                    offset: Offset(shimmer.value * 300, 0),
                    child: Container(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [
                            Colors.white.withOpacity(0.0),
                            Colors.white.withOpacity(0.12),
                            Colors.white.withOpacity(0.0),
                          ],
                          stops: const [0.0, 0.5, 1.0],
                          begin: Alignment.centerLeft,
                          end: Alignment.centerRight,
                        ),
                      ),
                    ),
                  ),
                ),
                const Center(
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.lock_open_outlined, color: Colors.white, size: 18),
                      SizedBox(width: 10),
                      Text(
                        'DECODE',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 15,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 2.5,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _LoadingButton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(14),
        color: _purple.withOpacity(0.3),
        border: Border.all(color: _purple.withOpacity(0.5)),
      ),
      child: const Center(
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            SizedBox(
              width: 16, height: 16,
              child: CircularProgressIndicator(strokeWidth: 2, color: _cyan),
            ),
            SizedBox(width: 12),
            Text('Analysing…', style: TextStyle(color: _cyan, fontSize: 14, fontWeight: FontWeight.w600, letterSpacing: 1)),
          ],
        ),
      ),
    );
  }
}

// ── Example chips ─────────────────────────────────────────────────────────────

class _ExampleChip extends StatelessWidget {
  final String label;
  final String text;
  final void Function(String) onTap;
  const _ExampleChip({required this.label, required this.text, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => onTap(text),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: _card,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: _purple.withOpacity(0.35)),
        ),
        child: Text(label, style: const TextStyle(color: _cyan, fontSize: 12, fontWeight: FontWeight.w500)),
      ),
    );
  }
}

// ── Dot grid background painter (public so analysis_screen can reuse) ─────────

class DotGridPainter extends CustomPainter {
  final double t;
  DotGridPainter(this.t);

  @override
  void paint(Canvas canvas, Size size) {
    const spacing = 38.0;
    final paint = Paint()..style = PaintingStyle.fill;
    final cx = size.width / 2;
    final cy = size.height / 3;

    for (double x = 0; x <= size.width + spacing; x += spacing) {
      for (double y = 0; y <= size.height + spacing; y += spacing) {
        final dist = math.sqrt(math.pow(x - cx, 2) + math.pow(y - cy, 2));
        final wave = math.sin(dist / 70 - t * math.pi * 2) * 0.5 + 0.5;
        final opacity = (wave * 0.07 + 0.015).clamp(0.0, 1.0);
        paint.color = _purple.withOpacity(opacity);
        canvas.drawCircle(Offset(x, y), 1.5, paint);
      }
    }
  }

  @override
  bool shouldRepaint(DotGridPainter old) => old.t != t;
}
