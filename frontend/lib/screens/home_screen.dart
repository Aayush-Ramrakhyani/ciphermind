/*
 * CipherMind home screen — input ciphertext and launch analysis.
 */

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/api_client.dart';
import '../core/constants.dart';
import '../core/theme.dart';
import 'analysis_screen.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  final TextEditingController _controller = TextEditingController();
  bool _isSubmitting = false;
  String? _error;

  Future<void> _submit() async {
    final text = _controller.text.trim();
    if (text.isEmpty) {
      setState(() => _error = 'Please enter a ciphertext to analyse.');
      return;
    }
    if (text.length > AppConstants.maxCiphertextLength) {
      setState(() => _error = 'Input exceeds ${AppConstants.maxCiphertextLength} characters.');
      return;
    }

    setState(() {
      _isSubmitting = true;
      _error = null;
    });

    try {
      final api = ref.read(apiClientProvider);
      final jobData = await api.submitAnalysis(text);
      if (!mounted) return;
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => AnalysisScreen(jobId: jobData['id'] as String),
        ),
      );
    } catch (e) {
      setState(() => _error = 'Analysis failed: ${e.toString().replaceAll('DioException', '')}');
    } finally {
      setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('CipherMind'),
        actions: [
          IconButton(
            icon: const Icon(Icons.history, color: AppTheme.textSecondary),
            tooltip: 'Analysis History',
            onPressed: () {},
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 8),
              Text(
                'Autonomous Cryptanalysis',
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  color: AppTheme.primaryCyan,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Paste any encrypted message. CipherMind will autonomously identify '
                'the cipher, recover the plaintext, and explain the cryptographic reasoning.',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 32),
              TextField(
                controller: _controller,
                maxLines: 8,
                maxLength: AppConstants.maxCiphertextLength,
                decoration: const InputDecoration(
                  labelText: 'Ciphertext',
                  hintText: 'KHOOR ZRUOG\nor paste Base64, Hex, Morse, etc.',
                  alignLabelWithHint: true,
                ),
                style: const TextStyle(
                  fontFamily: 'monospace',
                  color: AppTheme.textPrimary,
                  fontSize: 14,
                ),
              ),
              if (_error != null) ...[
                const SizedBox(height: 8),
                Text(
                  _error!,
                  style: const TextStyle(color: AppTheme.errorRed, fontSize: 13),
                ),
              ],
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _isSubmitting ? null : _submit,
                  icon: _isSubmitting
                      ? const SizedBox(
                          width: 16, height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.backgroundDark),
                        )
                      : const Icon(Icons.search),
                  label: Text(_isSubmitting ? 'Analysing...' : 'Analyse Ciphertext'),
                ),
              ),
              const SizedBox(height: 48),
              // Quick examples
              Text(
                'Try an example:',
                style: Theme.of(context).textTheme.labelLarge,
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  _ExampleChip(
                    label: 'Caesar ROT-3',
                    text: 'KHOOR ZRUOG — WKH TXLFN EURZQ IRA',
                    onTap: (t) => _controller.text = t,
                  ),
                  _ExampleChip(
                    label: 'Base64',
                    text: 'SGVsbG8sIFdvcmxkIQ==',
                    onTap: (t) => _controller.text = t,
                  ),
                  _ExampleChip(
                    label: 'Morse',
                    text: '.... . .-.. .-.. --- / .-- --- .-. .-.. -..',
                    onTap: (t) => _controller.text = t,
                  ),
                  _ExampleChip(
                    label: 'Hex',
                    text: '48656c6c6f2c20576f726c6421',
                    onTap: (t) => _controller.text = t,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}

class _ExampleChip extends StatelessWidget {
  final String label;
  final String text;
  final void Function(String) onTap;

  const _ExampleChip({required this.label, required this.text, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return ActionChip(
      label: Text(label, style: const TextStyle(fontSize: 12)),
      backgroundColor: AppTheme.cardDark,
      side: const BorderSide(color: AppTheme.primaryCyan, width: 1),
      labelStyle: const TextStyle(color: AppTheme.primaryCyan),
      onPressed: () => onTap(text),
    );
  }
}
