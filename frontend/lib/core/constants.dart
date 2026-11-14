/*
 * CipherMind app-wide constants.
 */

class AppConstants {
  static const String appName = 'CipherMind';
  static const String appVersion = '1.0.0';

  // API
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000/api/v1',
  );
  static const Duration connectTimeout = Duration(seconds: 10);
  static const Duration receiveTimeout = Duration(seconds: 30);

  // Limits
  static const int maxCiphertextLength = 50000;
  static const int playgroundMaxLength = 1000;
  static const int pollIntervalMs = 2000;
  static const int maxPollAttempts = 60; // 2 min max

  // Storage keys
  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
}
