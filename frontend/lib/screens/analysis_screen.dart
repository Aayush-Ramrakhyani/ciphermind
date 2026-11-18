/*
 * CipherMind analysis result screen — cyberpunk theme.
 * Animated sequence: ciphertext fade-in → scan sweep → typewriter decode reveal.
 */

import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/constants.dart';
import '../models/analysis_result.dart';
import 'home_screen.dart' show apiClientProvider, DotGridPainter;

// ── Design tokens (same as home_screen) ──────────────────────────────────────
const _bg      = Color(0xFF06080F);
const _card    = Color(0xFF131622);
const _purple  = Color(0xFF7C3AED);
const _cyan    = Color(0xFF06B6D4);
const _green   = Color(0xFF10B981);
const _amber   = Color(0xFFF59E0B);
const _text    = Color(0xFFF1F5F9);
const _subtext = Color(0xFF64748B);
const _border  = Color(0xFF1E2130);

class AnalysisScreen extends ConsumerStatefulWidget {
  final String? jobId;
  final Map<String, dynamic>? inlineResult;

  const AnalysisScreen({super.key, this.jobId, this.inlineResult})
      : assert(jobId != null || inlineResult != null);

  @override
  ConsumerState<AnalysisScreen> createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends ConsumerState<AnalysisScreen>
    with TickerProviderStateMixin {
  AnalysisResult? _result;
  bool _loading = true;
  String? _error;
  int _pollCount = 0;
  Timer? _timer;
  bool _showOthers = false;

  late AnimationController _bgController;
  late AnimationController _cipherFadeCtrl;   // encrypted block fade-in
  late AnimationController _scanCtrl;          // scan line sweep
  late AnimationController _decodeCtrl;        // decoded card slide-in
  late AnimationController _typewriterCtrl;    // letter-by-letter text
  late AnimationController _chipsCtrl;         // chips + others fade-in
  late AnimationController _pulseCtrl;         // glow pulse on decode card

  late Animation<double> _cipherFade;
  late Animation<double> _scanPos;             // 0→1 top→bottom of card
  late Animation<double> _scanFade;
  late Animation<Offset> _decodeSlide;
  late Animation<double> _decodeFade;
  late Animation<double> _chipsFade;
  late Animation<double> _glowPulse;

  @override
  void initState() {
    super.initState();
    _setupAnimations();
    if (widget.inlineResult != null) {
      _result = AnalysisResult.fromJson(widget.inlineResult!);
      _loading = false;
      _playSequence();
    } else {
      _fetchJob();
    }
  }

  void _setupAnimations() {
    _bgController = AnimationController(vsync: this, duration: const Duration(seconds: 6))..repeat();

    _cipherFadeCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 500));
    _cipherFade = CurvedAnimation(parent: _cipherFadeCtrl, curve: Curves.easeOut);

    _scanCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 700));
    _scanPos = CurvedAnimation(parent: _scanCtrl, curve: Curves.easeInOut);
    _scanFade = Tween<double>(begin: 1.0, end: 0.0).animate(
      CurvedAnimation(parent: _scanCtrl, curve: const Interval(0.75, 1.0, curve: Curves.easeOut)),
    );

    _decodeCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 500));
    _decodeSlide = Tween<Offset>(begin: const Offset(0, 0.25), end: Offset.zero).animate(
      CurvedAnimation(parent: _decodeCtrl, curve: Curves.easeOutCubic),
    );
    _decodeFade = CurvedAnimation(parent: _decodeCtrl, curve: Curves.easeOut);

    _typewriterCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1200));

    _chipsCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 400));
    _chipsFade = CurvedAnimation(parent: _chipsCtrl, curve: Curves.easeOut);

    _pulseCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 2000))..repeat(reverse: true);
    _glowPulse = Tween<double>(begin: 8.0, end: 24.0).animate(
      CurvedAnimation(parent: _pulseCtrl, curve: Curves.easeInOut),
    );
  }

  Future<void> _playSequence() async {
    final top = _result?.candidates.firstOrNull;
    final textLen = top?.plaintext.length ?? 0;

    // Typewriter duration scales with text length (min 600ms, max 2s)
    final twDuration = Duration(milliseconds: (textLen * 18).clamp(600, 2000));
    _typewriterCtrl.duration = twDuration;

    await Future.delayed(const Duration(milliseconds: 150));
    _cipherFadeCtrl.forward();

    await Future.delayed(const Duration(milliseconds: 600));
    _scanCtrl.forward();

    await Future.delayed(const Duration(milliseconds: 850));
    _decodeCtrl.forward();
    _typewriterCtrl.forward();

    await Future.delayed(Duration(milliseconds: twDuration.inMilliseconds + 200));
    _chipsCtrl.forward();
  }

  Future<void> _fetchJob() async {
    if (_pollCount > AppConstants.maxPollAttempts) {
      setState(() { _loading = false; _error = 'Taking too long. Please try again.'; });
      return;
    }
    try {
      final api = ref.read(apiClientProvider);
      final data = await api.getAnalysisJob(widget.jobId!);
      final job = AnalysisJob.fromJson(data);
      setState(() => _pollCount++);
      if (job.isPending) {
        _timer = Timer(Duration(milliseconds: AppConstants.pollIntervalMs), _fetchJob);
      } else {
        setState(() {
          _loading = false;
          _result = job.result;
          if (job.isFailed) _error = 'Analysis failed on server.';
        });
        if (_result != null) _playSequence();
      }
    } catch (e) {
      setState(() { _loading = false; _error = 'Failed: $e'; });
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    _bgController.dispose();
    _cipherFadeCtrl.dispose();
    _scanCtrl.dispose();
    _decodeCtrl.dispose();
    _typewriterCtrl.dispose();
    _chipsCtrl.dispose();
    _pulseCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      appBar: AppBar(
        backgroundColor: _bg,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: _subtext, size: 18),
          onPressed: () => Navigator.pop(context),
        ),
        title: ShaderMask(
          shaderCallback: (r) => const LinearGradient(colors: [_purple, _cyan])
              .createShader(r),
          child: const Text('CIPHERMIND',
              style: TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w900, letterSpacing: 3)),
        ),
        centerTitle: true,
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(
            height: 1,
            decoration: const BoxDecoration(
              gradient: LinearGradient(colors: [Colors.transparent, _purple, Colors.transparent]),
            ),
          ),
        ),
      ),
      body: Stack(
        children: [
          Positioned.fill(
            child: AnimatedBuilder(
              animation: _bgController,
              builder: (_, __) => CustomPaint(painter: DotGridPainter(_bgController.value)),
            ),
          ),
          _buildBody(),
        ],
      ),
    );
  }

  Widget _buildBody() {
    if (_error != null) return _buildError();
    if (_loading)       return _buildLoading();
    final result = _result;
    if (result == null || result.candidates.isEmpty) return _buildNoResult();
    return _buildResult(result);
  }

  // ── Loading ────────────────────────────────────────────────────────────────

  Widget _buildLoading() {
    return Center(
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        AnimatedBuilder(
          animation: _pulseCtrl,
          builder: (_, __) => Container(
            width: 72, height: 72,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: _purple.withOpacity(0.1),
              border: Border.all(color: _purple.withOpacity(0.5)),
              boxShadow: [BoxShadow(color: _purple.withOpacity(0.3), blurRadius: _glowPulse.value, spreadRadius: 2)],
            ),
            child: const Icon(Icons.lock_open_outlined, color: _purple, size: 30),
          ),
        ),
        const SizedBox(height: 20),
        const Text('Cracking the cipher…',
            style: TextStyle(color: _text, fontSize: 15, fontWeight: FontWeight.w600)),
        const SizedBox(height: 6),
        const Text('Running statistical analysis and all cipher solvers',
            style: TextStyle(color: _subtext, fontSize: 12), textAlign: TextAlign.center),
        const SizedBox(height: 28),
        SizedBox(
          width: 160,
          child: LinearProgressIndicator(
            backgroundColor: _border,
            valueColor: const AlwaysStoppedAnimation(_purple),
          ),
        ),
      ]),
    );
  }

  // ── Error ──────────────────────────────────────────────────────────────────

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.lock_outline, color: Color(0xFFF87171), size: 48),
          const SizedBox(height: 16),
          Text(_error!, style: const TextStyle(color: Color(0xFFF87171), fontSize: 13), textAlign: TextAlign.center),
          const SizedBox(height: 24),
          _GlowButton(label: 'Go Back', onTap: () => Navigator.pop(context)),
        ]),
      ),
    );
  }

  Widget _buildNoResult() {
    return Center(
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        const Icon(Icons.search_off, color: _subtext, size: 48),
        const SizedBox(height: 16),
        const Text('No decryption found.', style: TextStyle(color: _subtext, fontSize: 14)),
        const SizedBox(height: 24),
        _GlowButton(label: 'Try Again', onTap: () => Navigator.pop(context)),
      ]),
    );
  }

  // ── Main result ────────────────────────────────────────────────────────────

  Widget _buildResult(AnalysisResult result) {
    final top = result.candidates.first;
    final others = result.candidates.skip(1).toList();

    return SingleChildScrollView(
      physics: const BouncingScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 48),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Encrypted block
          FadeTransition(
            opacity: _cipherFade,
            child: _EncryptedBlock(
              ciphertext: result.ciphertext,
              scanPos: _scanPos,
              scanFade: _scanFade,
              scanCtrl: _scanCtrl,
            ),
          ),

          const SizedBox(height: 20),

          // Decoded heading arrow
          FadeTransition(
            opacity: _decodeFade,
            child: _DecodeArrow(),
          ),

          const SizedBox(height: 16),

          // Decoded card with typewriter
          SlideTransition(
            position: _decodeSlide,
            child: FadeTransition(
              opacity: _decodeFade,
              child: _DecodedCard(
                candidate: top,
                typewriterCtrl: _typewriterCtrl,
                glowPulse: _glowPulse,
              ),
            ),
          ),

          const SizedBox(height: 20),

          // Method + key chips
          FadeTransition(
            opacity: _chipsFade,
            child: _MethodRow(candidate: top),
          ),

          if (others.isNotEmpty) ...[
            const SizedBox(height: 28),
            FadeTransition(
              opacity: _chipsFade,
              child: _OthersSection(
                others: others,
                expanded: _showOthers,
                onToggle: () => setState(() => _showOthers = !_showOthers),
              ),
            ),
          ],

          const SizedBox(height: 16),
          FadeTransition(
            opacity: _chipsFade,
            child: Text(
              'Processed in ${result.processingTimeMs}ms',
              style: const TextStyle(color: _subtext, fontSize: 10, letterSpacing: 0.5),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Encrypted block with scan line ───────────────────────────────────────────

class _EncryptedBlock extends StatelessWidget {
  final String ciphertext;
  final Animation<double> scanPos;
  final Animation<double> scanFade;
  final AnimationController scanCtrl;
  const _EncryptedBlock({
    required this.ciphertext,
    required this.scanPos,
    required this.scanFade,
    required this.scanCtrl,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: _amber.withOpacity(0.1),
              borderRadius: BorderRadius.circular(4),
              border: Border.all(color: _amber.withOpacity(0.4)),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.lock_outline, color: _amber, size: 10),
                SizedBox(width: 4),
                Text('ENCRYPTED', style: TextStyle(color: _amber, fontSize: 9, fontWeight: FontWeight.w700, letterSpacing: 1.2)),
              ],
            ),
          ),
        ]),
        const SizedBox(height: 8),
        Container(
          width: double.infinity,
          decoration: BoxDecoration(
            color: _card,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: _amber.withOpacity(0.2)),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: Stack(
              children: [
                Padding(
                  padding: const EdgeInsets.all(14),
                  child: Text(
                    ciphertext,
                    style: TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 13,
                      color: _subtext.withOpacity(0.8),
                      height: 1.6,
                    ),
                  ),
                ),
                // Scan line
                AnimatedBuilder(
                  animation: scanPos,
                  builder: (_, __) {
                    if (!scanCtrl.isAnimating && scanCtrl.value == 0) {
                      return const SizedBox.shrink();
                    }
                    return Positioned(
                      top: scanPos.value * 80,
                      left: 0, right: 0,
                      child: FadeTransition(
                        opacity: scanFade,
                        child: Container(
                          height: 2,
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [
                                Colors.transparent,
                                _cyan.withOpacity(0.9),
                                _purple.withOpacity(0.9),
                                Colors.transparent,
                              ],
                            ),
                            boxShadow: [BoxShadow(color: _cyan.withOpacity(0.6), blurRadius: 8, spreadRadius: 1)],
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

// ── Decode arrow divider ──────────────────────────────────────────────────────

class _DecodeArrow extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Row(children: [
      Expanded(
        child: Container(
          height: 1,
          decoration: BoxDecoration(
            gradient: LinearGradient(colors: [Colors.transparent, _green.withOpacity(0.4)]),
          ),
        ),
      ),
      const SizedBox(width: 10),
      Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: _green.withOpacity(0.1),
          borderRadius: BorderRadius.circular(4),
          border: Border.all(color: _green.withOpacity(0.4)),
        ),
        child: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.lock_open, color: _green, size: 10),
            SizedBox(width: 4),
            Text('DECRYPTED', style: TextStyle(color: _green, fontSize: 9, fontWeight: FontWeight.w700, letterSpacing: 1.2)),
          ],
        ),
      ),
      const SizedBox(width: 10),
      Expanded(
        child: Container(
          height: 1,
          decoration: BoxDecoration(
            gradient: LinearGradient(colors: [_green.withOpacity(0.4), Colors.transparent]),
          ),
        ),
      ),
    ]);
  }
}

// ── Decoded card with typewriter ──────────────────────────────────────────────

class _DecodedCard extends StatefulWidget {
  final CipherCandidate candidate;
  final AnimationController typewriterCtrl;
  final Animation<double> glowPulse;
  const _DecodedCard({required this.candidate, required this.typewriterCtrl, required this.glowPulse});

  @override
  State<_DecodedCard> createState() => _DecodedCardState();
}

class _DecodedCardState extends State<_DecodedCard> {
  bool _copied = false;

  void _copy() async {
    await Clipboard.setData(ClipboardData(text: widget.candidate.plaintext));
    setState(() => _copied = true);
    await Future.delayed(const Duration(seconds: 2));
    if (mounted) setState(() => _copied = false);
  }

  @override
  Widget build(BuildContext context) {
    final fullText = widget.candidate.plaintext;

    return AnimatedBuilder(
      animation: Listenable.merge([widget.typewriterCtrl, widget.glowPulse]),
      builder: (_, __) {
        final visibleCount = (widget.typewriterCtrl.value * fullText.length).round().clamp(0, fullText.length);
        final displayText = fullText.substring(0, visibleCount);
        final isTyping = widget.typewriterCtrl.isAnimating;
        final glowR = widget.glowPulse.value;

        return Container(
          width: double.infinity,
          decoration: BoxDecoration(
            color: _card,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: _green.withOpacity(0.35), width: 1.5),
            boxShadow: [BoxShadow(color: _green.withOpacity(0.12), blurRadius: glowR, spreadRadius: 1)],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                decoration: BoxDecoration(
                  color: _green.withOpacity(0.07),
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
                ),
                child: Row(children: [
                  Container(
                    width: 7, height: 7,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _green,
                      boxShadow: [BoxShadow(color: _green.withOpacity(0.7), blurRadius: 6)],
                    ),
                  ),
                  const SizedBox(width: 8),
                  const Text('BEST MATCH', style: TextStyle(color: _green, fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 1.5)),
                  const Spacer(),
                  _ConfidenceBadge(confidence: widget.candidate.confidence),
                ]),
              ),
              // Typewriter text
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
                child: RichText(
                  text: TextSpan(
                    children: [
                      TextSpan(
                        text: displayText,
                        style: const TextStyle(
                          color: _text,
                          fontSize: 15,
                          fontWeight: FontWeight.w500,
                          height: 1.75,
                          fontFamily: 'monospace',
                        ),
                      ),
                      if (isTyping)
                        WidgetSpan(
                          child: Container(
                            width: 2, height: 18,
                            margin: const EdgeInsets.only(left: 1, bottom: 2),
                            color: _cyan,
                          ),
                        ),
                    ],
                  ),
                ),
              ),
              // Copy button
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 4, 16, 14),
                child: GestureDetector(
                  onTap: _copy,
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
                    decoration: BoxDecoration(
                      color: _copied ? _green.withOpacity(0.12) : _card,
                      borderRadius: BorderRadius.circular(7),
                      border: Border.all(
                        color: _copied ? _green.withOpacity(0.5) : _border,
                      ),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(_copied ? Icons.check : Icons.copy_outlined,
                            size: 13, color: _copied ? _green : _subtext),
                        const SizedBox(width: 6),
                        Text(_copied ? 'Copied!' : 'Copy text',
                            style: TextStyle(color: _copied ? _green : _subtext, fontSize: 11, fontWeight: FontWeight.w500)),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

// ── Confidence badge ──────────────────────────────────────────────────────────

class _ConfidenceBadge extends StatelessWidget {
  final String confidence;
  const _ConfidenceBadge({required this.confidence});

  @override
  Widget build(BuildContext context) {
    final Color color;
    final String label;
    switch (confidence) {
      case 'high':     color = _green; label = 'High Confidence'; break;
      case 'likely':   color = _amber; label = 'Likely'; break;
      case 'possible': color = const Color(0xFFFF9800); label = 'Possible'; break;
      default:         color = _subtext; label = 'Unknown';
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.4)),
      ),
      child: Text(label, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.w700)),
    );
  }
}

// ── Method / key chips ────────────────────────────────────────────────────────

class _MethodRow extends StatelessWidget {
  final CipherCandidate candidate;
  const _MethodRow({required this.candidate});

  @override
  Widget build(BuildContext context) {
    final keyStr = candidate.key?.toString() ?? '';
    final showKey = keyStr.isNotEmpty && keyStr.length < 50;

    return Wrap(
      spacing: 8, runSpacing: 8,
      children: [
        _InfoChip(
          icon: Icons.lock_open_outlined,
          label: _friendlyName(candidate.cipherType),
          color: _purple,
        ),
        if (showKey)
          _InfoChip(
            icon: Icons.key_outlined,
            label: 'Key: $keyStr',
            color: _cyan,
          ),
      ],
    );
  }
}

class _InfoChip extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  const _InfoChip({required this.icon, required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.07),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 12, color: color),
        const SizedBox(width: 6),
        Text(label, style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.w600)),
      ]),
    );
  }
}

// ── Others section ────────────────────────────────────────────────────────────

class _OthersSection extends StatelessWidget {
  final List<CipherCandidate> others;
  final bool expanded;
  final VoidCallback onToggle;
  const _OthersSection({required this.others, required this.expanded, required this.onToggle});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        GestureDetector(
          onTap: onToggle,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: _card,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: _border),
            ),
            child: Row(children: [
              const Text('Other possibilities',
                  style: TextStyle(color: _subtext, fontSize: 12, fontWeight: FontWeight.w500)),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 1),
                decoration: BoxDecoration(
                  color: _purple.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text('${others.length}',
                    style: const TextStyle(color: _purple, fontSize: 10, fontWeight: FontWeight.w700)),
              ),
              const Spacer(),
              AnimatedRotation(
                turns: expanded ? 0.5 : 0,
                duration: const Duration(milliseconds: 200),
                child: const Icon(Icons.keyboard_arrow_down, color: _subtext, size: 16),
              ),
            ]),
          ),
        ),
        AnimatedCrossFade(
          duration: const Duration(milliseconds: 250),
          crossFadeState: expanded ? CrossFadeState.showSecond : CrossFadeState.showFirst,
          firstChild: const SizedBox.shrink(),
          secondChild: Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Column(children: others.map((c) => _OtherCard(candidate: c)).toList()),
          ),
        ),
      ],
    );
  }
}

class _OtherCard extends StatelessWidget {
  final CipherCandidate candidate;
  const _OtherCard({required this.candidate});

  @override
  Widget build(BuildContext context) {
    final keyStr = candidate.key?.toString() ?? '';
    final showKey = keyStr.isNotEmpty && keyStr.length < 40;

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: _card,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: _border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Text(_friendlyName(candidate.cipherType),
                style: const TextStyle(color: _subtext, fontSize: 11, fontWeight: FontWeight.w600)),
            if (showKey) ...[
              const SizedBox(width: 8),
              Text('key: $keyStr',
                  style: const TextStyle(color: _cyan, fontSize: 10, fontFamily: 'monospace')),
            ],
            const Spacer(),
            Text(candidate.languageScore.toStringAsFixed(3),
                style: const TextStyle(color: _subtext, fontSize: 10)),
          ]),
          const SizedBox(height: 6),
          Text(
            candidate.plaintext.length > 100
                ? '${candidate.plaintext.substring(0, 100)}…'
                : candidate.plaintext,
            style: const TextStyle(
              color: _text,
              fontSize: 12,
              fontFamily: 'monospace',
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }
}

// ── Glow button ───────────────────────────────────────────────────────────────

class _GlowButton extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  const _GlowButton({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 12),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(10),
          gradient: const LinearGradient(colors: [_purple, _cyan]),
          boxShadow: [BoxShadow(color: _purple.withOpacity(0.4), blurRadius: 16, offset: const Offset(0, 4))],
        ),
        child: Text(label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13)),
      ),
    );
  }
}

// ── Cipher friendly names ─────────────────────────────────────────────────────

String _friendlyName(String cipherType) {
  switch (cipherType.toLowerCase()) {
    case 'caesar':         return 'Alphabet Shift (Caesar)';
    case 'rot13':          return 'Flip 13 Letters (ROT-13)';
    case 'rot5':           return 'Flip 5 Numbers (ROT-5)';
    case 'rot18':          return 'Flip Letters & Numbers (ROT-18)';
    case 'rot47':          return 'Flip Everything (ROT-47)';
    case 'atbash':         return 'Mirror Alphabet (Atbash)';
    case 'affine':         return 'Math Shuffle (Affine)';
    case 'vigenere':       return 'Password Cipher (Vigenère)';
    case 'monoalphabetic': return 'Letter Swap Cipher';
    case 'playfair':       return 'Grid Cipher (Playfair)';
    case 'rail_fence':     return 'Zigzag Cipher (Rail Fence)';
    case 'columnar':       return 'Column Shuffle Cipher';
    case 'base64':         return 'Computer Text Code (Base64)';
    case 'hex':            return 'Number Code (Hex)';
    case 'binary':         return 'Computer On/Off Code (Binary)';
    case 'morse':          return 'Dot-Dash Code (Morse)';
    case 'url_encoding':   return 'Web Link Code (URL)';
    default:               return cipherType.toUpperCase();
  }
}
