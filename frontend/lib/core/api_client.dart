/*
 * CipherMind API client.
 * Handles JWT auth, token refresh, and all API calls.
 */

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'constants.dart';

class ApiClient {
  late final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  ApiClient() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConstants.baseUrl,
      connectTimeout: AppConstants.connectTimeout,
      receiveTimeout: AppConstants.receiveTimeout,
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: _onRequest,
        onError: _onError,
      ),
    );
  }

  Future<void> _onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _storage.read(key: AppConstants.accessTokenKey);
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  Future<void> _onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    if (err.response?.statusCode == 401) {
      final refreshed = await _refreshToken();
      if (refreshed) {
        final token = await _storage.read(key: AppConstants.accessTokenKey);
        err.requestOptions.headers['Authorization'] = 'Bearer $token';
        final response = await _dio.fetch(err.requestOptions);
        handler.resolve(response);
        return;
      }
    }
    handler.next(err);
  }

  Future<bool> _refreshToken() async {
    try {
      final refreshToken = await _storage.read(key: AppConstants.refreshTokenKey);
      if (refreshToken == null) return false;
      final response = await _dio.post('/auth/token/refresh/', data: {'refresh': refreshToken});
      await _storage.write(key: AppConstants.accessTokenKey, value: response.data['access']);
      return true;
    } catch (_) {
      await logout();
      return false;
    }
  }

  Future<void> login(String email, String password) async {
    final response = await _dio.post('/auth/login/', data: {
      'email': email,
      'password': password,
    });
    await _storage.write(key: AppConstants.accessTokenKey, value: response.data['access']);
    await _storage.write(key: AppConstants.refreshTokenKey, value: response.data['refresh']);
  }

  Future<Map<String, dynamic>> register(String email, String username, String password) async {
    final response = await _dio.post('/auth/register/', data: {
      'email': email,
      'username': username,
      'password': password,
      'password2': password,
    });
    await _storage.write(key: AppConstants.accessTokenKey, value: response.data['tokens']['access']);
    await _storage.write(key: AppConstants.refreshTokenKey, value: response.data['tokens']['refresh']);
    return response.data;
  }

  Future<void> logout() async {
    final refreshToken = await _storage.read(key: AppConstants.refreshTokenKey);
    if (refreshToken != null) {
      try {
        await _dio.post('/auth/logout/', data: {'refresh': refreshToken});
      } catch (_) {}
    }
    await _storage.deleteAll();
  }

  Future<bool> isAuthenticated() async {
    return await _storage.read(key: AppConstants.accessTokenKey) != null;
  }

  Future<Map<String, dynamic>> submitAnalysis(String ciphertext) async {
    final response = await _dio.post('/analysis/', data: {'ciphertext': ciphertext});
    return response.data;
  }

  Future<Map<String, dynamic>> getAnalysisJob(String jobId) async {
    final response = await _dio.get('/analysis/$jobId/');
    return response.data;
  }

  Future<List<dynamic>> listAnalysisJobs() async {
    final response = await _dio.get('/analysis/list/');
    return response.data['results'] ?? response.data;
  }

  Future<Map<String, dynamic>> playground(String ciphertext) async {
    final response = await _dio.post('/playground/', data: {'ciphertext': ciphertext});
    return response.data;
  }
}
