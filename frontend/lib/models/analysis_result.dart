/*
 * CipherMind analysis data models.
 */

class CipherCandidate {
  final String cipherType;
  final String plaintext;
  final dynamic key;
  final String confidence;
  final double languageScore;
  final String explanation;
  final Map<String, dynamic> metadata;

  const CipherCandidate({
    required this.cipherType,
    required this.plaintext,
    required this.key,
    required this.confidence,
    required this.languageScore,
    required this.explanation,
    this.metadata = const {},
  });

  factory CipherCandidate.fromJson(Map<String, dynamic> json) => CipherCandidate(
        cipherType: json['cipher_type'] as String,
        plaintext: json['plaintext'] as String,
        key: json['key'],
        confidence: json['confidence'] as String,
        languageScore: (json['language_score'] as num).toDouble(),
        explanation: json['explanation'] as String,
        metadata: (json['metadata'] as Map<String, dynamic>?) ?? {},
      );

  String get confidenceEmoji {
    switch (confidence) {
      case 'high': return '✅';
      case 'likely': return '🟡';
      case 'possible': return '🟠';
      default: return '❓';
    }
  }
}

class AnalysisResult {
  final String ciphertext;
  final List<CipherCandidate> candidates;
  final List<String> detectedEncodings;
  final Map<String, dynamic> statisticalSummary;
  final List<dynamic> multilayerChains;
  final String? aiExplanation;
  final int processingTimeMs;

  const AnalysisResult({
    required this.ciphertext,
    required this.candidates,
    required this.detectedEncodings,
    required this.statisticalSummary,
    required this.multilayerChains,
    this.aiExplanation,
    required this.processingTimeMs,
  });

  factory AnalysisResult.fromJson(Map<String, dynamic> json) => AnalysisResult(
        ciphertext: json['ciphertext'] as String? ?? '',
        candidates: (json['candidates'] as List<dynamic>? ?? [])
            .map((e) => CipherCandidate.fromJson(e as Map<String, dynamic>))
            .toList(),
        detectedEncodings: (json['detected_encodings'] as List<dynamic>? ?? [])
            .map((e) => e.toString())
            .toList(),
        statisticalSummary: (json['statistical_summary'] as Map<String, dynamic>?) ?? {},
        multilayerChains: (json['multilayer_chains'] as List<dynamic>?) ?? [],
        aiExplanation: json['ai_explanation'] as String?,
        processingTimeMs: (json['processing_time_ms'] as num?)?.toInt() ?? 0,
      );
}

class AnalysisJob {
  final String id;
  final String ciphertextPreview;
  final String status;
  final DateTime createdAt;
  final AnalysisResult? result;

  const AnalysisJob({
    required this.id,
    required this.ciphertextPreview,
    required this.status,
    required this.createdAt,
    this.result,
  });

  factory AnalysisJob.fromJson(Map<String, dynamic> json) => AnalysisJob(
        id: json['id'] as String,
        ciphertextPreview: json['ciphertext_preview'] as String? ?? '',
        status: json['status'] as String,
        createdAt: DateTime.parse(json['created_at'] as String),
        result: json['result'] != null
            ? AnalysisResult.fromJson(json['result'] as Map<String, dynamic>)
            : null,
      );

  bool get isDone => status == 'done';
  bool get isFailed => status == 'failed';
  bool get isPending => status == 'pending' || status == 'running';
}
