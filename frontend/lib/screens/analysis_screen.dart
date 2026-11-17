/*
 * CipherMind analysis result screen.
 * Polls job status until done, then displays ranked candidates and stats.
 */

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/api_client.dart';
import '../core/constants.dart';
import '../core/theme.dart';
import '../models/analysis_result.dart';
import 'home_screen.dart';

class AnalysisScreen extends ConsumerStatefulWidget {
  final String? jobId;
  final Map<String, dynamic>? inlineResult;

  const AnalysisScreen({super.key, this.jobId, this.inlineResult})
      : assert(jobId != null || inlineResult != null);

  @override
  ConsumerState<AnalysisScreen> createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends ConsumerState<AnalysisScreen> {
  AnalysisResult? _result;
  bool _loading = true;
  String? _error;
  int _pollCount = 0;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    if (widget.inlineResult != null) {
      // Playground: results already available, no polling needed
      _result = AnalysisResult.fromJson(widget.inlineResult!);
      _loading = false;
    } else {
      _fetchJob();
    }
  }

  Future<void> _fetchJob() async {
    if (_pollCount > AppConstants.maxPollAttempts) {
      setState(() {
        _loading = false;
        _error = 'Analysis is taking too long. Please try again.';
      });
      return;
    }
    try {
      final api = ref.read(apiClientProvider);
      final data = await api.getAnalysisJob(widget.jobId!);
      final job = AnalysisJob.fromJson(data);
      setState(() => _pollCount++);
      if (job.isPending) {
        _timer = Timer(
          Duration(milliseconds: AppConstants.pollIntervalMs),
          _fetchJob,
        );
      } else {
        setState(() {
          _loading = false;
          _result = job.result;
          if (job.isFailed) _error = 'Analysis failed on the server.';
        });
      }
    } catch (e) {
      setState(() {
        _loading = false;
        _error = 'Failed to fetch analysis: $e';
      });
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Analysis Result'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, color: AppTheme.errorRed, size: 48),
              const SizedBox(height: 16),
              Text(_error!, style: const TextStyle(color: AppTheme.errorRed)),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Go Back'),
              ),
            ],
          ),
        ),
      );
    }

    if (_loading) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const CircularProgressIndicator(color: AppTheme.primaryCyan),
            const SizedBox(height: 20),
            Text('Analysing ciphertext...', style: Theme.of(context).textTheme.bodyLarge),
            const SizedBox(height: 8),
            Text('Running cipher solvers and statistical analysis',
                style: Theme.of(context).textTheme.bodyMedium),
          ],
        ),
      );
    }

    final result = _result;
    if (result == null) {
      return const Center(child: Text('No result available.'));
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _StatsSummaryCard(summary: result.statisticalSummary),
          const SizedBox(height: 16),
          _CandidatesSection(candidates: result.candidates),
          if (result.multilayerChains.isNotEmpty) ...[
            const SizedBox(height: 16),
            _MultilayerSection(chains: result.multilayerChains),
          ],
          if (result.aiExplanation != null && result.aiExplanation!.isNotEmpty) ...[
            const SizedBox(height: 16),
            _AiExplanationCard(explanation: result.aiExplanation!),
          ],
          const SizedBox(height: 8),
          Text(
            'Processing time: ${result.processingTimeMs}ms',
            style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }
}

class _StatsSummaryCard extends StatelessWidget {
  final Map<String, dynamic> summary;
  const _StatsSummaryCard({required this.summary});

  @override
  Widget build(BuildContext context) {
    return Card(
      color: AppTheme.cardDark,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Statistical Analysis', style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 12),
            Wrap(
              spacing: 16,
              runSpacing: 8,
              children: [
                _StatChip('IoC', '${summary['index_of_coincidence'] ?? '—'}'),
                _StatChip('χ²', '${summary['chi_squared'] ?? '—'}'),
                _StatChip('Type', '${summary['cipher_type_hint'] ?? '—'}'),
                _StatChip('Length', '${summary['length'] ?? '—'}'),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _StatChip extends StatelessWidget {
  final String label;
  final String value;
  const _StatChip(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: AppTheme.surfaceDark,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: const Color(0xFF30363D)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text('$label: ', style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
          Text(value, style: const TextStyle(color: AppTheme.primaryCyan, fontSize: 12, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}

class _CandidatesSection extends StatelessWidget {
  final List<CipherCandidate> candidates;
  const _CandidatesSection({required this.candidates});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Decryption Candidates', style: Theme.of(context).textTheme.labelLarge),
        const SizedBox(height: 8),
        if (candidates.isEmpty)
          const Text('No candidates found.', style: TextStyle(color: AppTheme.textSecondary))
        else
          ...candidates.asMap().entries.map((e) => _CandidateCard(
                candidate: e.value,
                rank: e.key + 1,
              )),
      ],
    );
  }
}

String _friendlyName(String cipherType) {
  switch (cipherType.toLowerCase()) {
    case 'caesar':      return 'Alphabet Shift (Caesar)';
    case 'rot13':       return 'Flip 13 Letters (ROT-13)';
    case 'rot5':        return 'Flip 5 Numbers (ROT-5)';
    case 'rot18':       return 'Flip Letters & Numbers (ROT-18)';
    case 'rot47':       return 'Flip Everything (ROT-47)';
    case 'atbash':      return 'Mirror Alphabet (Atbash)';
    case 'affine':      return 'Math Shuffle (Affine)';
    case 'vigenere':    return 'Password Cipher (Vigenère)';
    case 'monoalphabetic': return 'Letter Swap Cipher';
    case 'playfair':    return 'Grid Cipher (Playfair)';
    case 'rail_fence':  return 'Zigzag Cipher (Rail Fence)';
    case 'columnar':    return 'Column Shuffle Cipher';
    case 'base64':      return 'Computer Text Code (Base64)';
    case 'hex':         return 'Number Code (Hex)';
    case 'binary':      return 'Computer On/Off Code (Binary)';
    case 'morse':       return 'Dot-Dash Code (Morse)';
    case 'url_encoding': return 'Web Link Code (URL)';
    default:            return cipherType.toUpperCase();
  }
}

class _CandidateCard extends StatefulWidget {
  final CipherCandidate candidate;
  final int rank;
  const _CandidateCard({required this.candidate, required this.rank});

  @override
  State<_CandidateCard> createState() => _CandidateCardState();
}

class _CandidateCardState extends State<_CandidateCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final c = widget.candidate;
    final isTop = widget.rank == 1;
    return Card(
      color: isTop ? const Color(0xFF1C2A1C) : AppTheme.cardDark,
      margin: const EdgeInsets.only(bottom: 8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(
          color: isTop ? AppTheme.successGreen : const Color(0xFF30363D),
          width: isTop ? 1.5 : 1,
        ),
      ),
      child: InkWell(
        onTap: () => setState(() => _expanded = !_expanded),
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Text('${c.confidenceEmoji} ', style: const TextStyle(fontSize: 16)),
                  Text(
                    '#${widget.rank} ${_friendlyName(c.cipherType)}',
                    style: TextStyle(
                      color: isTop ? AppTheme.successGreen : AppTheme.textPrimary,
                      fontWeight: FontWeight.w600,
                      fontSize: 13,
                    ),
                  ),
                  const Spacer(),
                  Text(
                    'Score: ${c.languageScore.toStringAsFixed(3)}',
                    style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
                  ),
                  const SizedBox(width: 8),
                  Icon(
                    _expanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                    color: AppTheme.textSecondary,
                    size: 18,
                  ),
                ],
              ),
              const SizedBox(height: 8),
              GestureDetector(
                onLongPress: () {
                  Clipboard.setData(ClipboardData(text: c.plaintext));
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Copied to clipboard')),
                  );
                },
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppTheme.surfaceDark,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    (!_expanded && c.plaintext.length > 150)
                        ? '${c.plaintext.substring(0, 150)}...'
                        : c.plaintext,
                    style: const TextStyle(fontFamily: 'monospace', fontSize: 13, color: AppTheme.textPrimary),
                  ),
                ),
              ),
              if (_expanded) ...[
                const SizedBox(height: 10),
                Text(
                  c.explanation,
                  style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
                ),
                const SizedBox(height: 6),
                Text(
                  'Key: ${c.key}',
                  style: const TextStyle(color: AppTheme.primaryCyan, fontSize: 11, fontFamily: 'monospace'),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _MultilayerSection extends StatelessWidget {
  final List<dynamic> chains;
  const _MultilayerSection({required this.chains});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Multi-layer Chains Detected', style: Theme.of(context).textTheme.labelLarge),
        const SizedBox(height: 8),
        ...chains.map((chain) => _ChainCard(chain: chain as Map<String, dynamic>)),
      ],
    );
  }
}

class _ChainCard extends StatelessWidget {
  final Map<String, dynamic> chain;
  const _ChainCard({required this.chain});

  @override
  Widget build(BuildContext context) {
    final steps = (chain['steps'] as List<dynamic>? ?? []);
    return Card(
      color: AppTheme.cardDark,
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: steps.asMap().entries.expand((e) {
                final step = e.value as Map<String, dynamic>;
                return [
                  Text(
                    step['transform'] ?? '',
                    style: const TextStyle(color: AppTheme.primaryCyan, fontSize: 12),
                  ),
                  if (e.key < steps.length - 1)
                    const Text(' → ', style: TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                ];
              }).toList(),
            ),
            const SizedBox(height: 6),
            Text(
              '${chain['plaintext'] ?? ''}'.length > 100
                  ? '${chain['plaintext']}'.substring(0, 100)
                  : '${chain['plaintext'] ?? ''}',
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12, color: AppTheme.textPrimary),
            ),
          ],
        ),
      ),
    );
  }
}

class _AiExplanationCard extends StatelessWidget {
  final String explanation;
  const _AiExplanationCard({required this.explanation});

  @override
  Widget build(BuildContext context) {
    return Card(
      color: const Color(0xFF1A1A2E),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: const BorderSide(color: Color(0xFF4040FF), width: 1),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.psychology, color: AppTheme.primaryCyan, size: 18),
                SizedBox(width: 8),
                Text('AI Cryptanalysis Reasoning', style: TextStyle(color: AppTheme.primaryCyan, fontWeight: FontWeight.w600)),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              explanation,
              style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13, height: 1.6),
            ),
          ],
        ),
      ),
    );
  }
}
