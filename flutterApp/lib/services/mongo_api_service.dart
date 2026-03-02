import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config/app_config.dart';

/// Low-level HTTP client for the MongoDB backend.
/// Handles JWT token storage and authenticated requests.
class MongoApiService {
  static const _tokenKey = 'mongo_jwt_token';

  String? _token;

  // ─── Token management ──────────────────────────────────────────────────────
  Future<void> loadToken() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString(_tokenKey);
  }

  Future<void> saveToken(String token) async {
    _token = token;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
  }

  Future<void> clearToken() async {
    _token = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
  }

  bool get hasToken => _token != null && _token!.isNotEmpty;

  // ─── HTTP helpers ──────────────────────────────────────────────────────────
  Future<void> _ensureToken() async {
    if (_token == null) await loadToken();
  }

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  String _url(String path) => '${AppConfig.baseUrl}$path';

  Future<Map<String, dynamic>> get(String path) async {
    await _ensureToken();
    final res = await http.get(Uri.parse(_url(path)), headers: _headers)
        .timeout(const Duration(seconds: 15));
    return _parse(res);
  }

  Future<Map<String, dynamic>> post(String path, Map<String, dynamic> body) async {
    await _ensureToken();
    final res = await http.post(
      Uri.parse(_url(path)),
      headers: _headers,
      body: jsonEncode(body),
    ).timeout(const Duration(seconds: 15));
    return _parse(res);
  }

  Future<Map<String, dynamic>> put(String path, Map<String, dynamic> body) async {
    await _ensureToken();
    final res = await http.put(
      Uri.parse(_url(path)),
      headers: _headers,
      body: jsonEncode(body),
    ).timeout(const Duration(seconds: 15));
    return _parse(res);
  }

  Future<Map<String, dynamic>> delete(String path) async {
    await _ensureToken();
    final res = await http.delete(Uri.parse(_url(path)), headers: _headers)
        .timeout(const Duration(seconds: 15));
    return _parse(res);
  }

  Future<List<dynamic>> getList(String path) async {
    await _ensureToken();
    final res = await http.get(Uri.parse(_url(path)), headers: _headers)
        .timeout(const Duration(seconds: 15));
    if (res.statusCode >= 200 && res.statusCode < 300) {
      return jsonDecode(res.body) as List<dynamic>;
    }
    final err = jsonDecode(res.body);
    throw Exception(err['error'] ?? 'HTTP ${res.statusCode}');
  }

  Map<String, dynamic> _parse(http.Response res) {
    final body = jsonDecode(res.body);
    if (res.statusCode >= 200 && res.statusCode < 300) {
      return body as Map<String, dynamic>;
    }
    throw Exception((body as Map)['error'] ?? 'HTTP ${res.statusCode}');
  }

  // ─── Auth endpoints ────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> signup(String email, String password, String displayName) async {
    final res = await post('/auth/signup', {
      'email': email,
      'password': password,
      'displayName': displayName,
    });
    await saveToken(res['token'] as String);
    return res['user'] as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> signin(String email, String password) async {
    final res = await post('/auth/signin', {'email': email, 'password': password});
    await saveToken(res['token'] as String);
    return res['user'] as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>?> me() async {
    if (!hasToken) return null;
    try {
      final res = await get('/auth/me');
      return res['user'] as Map<String, dynamic>;
    } catch (_) {
      await clearToken();
      return null;
    }
  }

  Future<void> signout() => clearToken();

  // ─── Project endpoints ─────────────────────────────────────────────────────
  Future<List<dynamic>> getProjects() => getList('/projects');

  Future<Map<String, dynamic>> createProject(Map<String, dynamic> data) =>
      post('/projects', data);

  Future<Map<String, dynamic>> getProject(String pid) => get('/projects/$pid');

  Future<void> updateProject(String pid, Map<String, dynamic> data) =>
      put('/projects/$pid', data);

  Future<void> deleteProject(String pid) => delete('/projects/$pid');

  // ─── Subcollection endpoints ───────────────────────────────────────────────
  Future<List<dynamic>> getSub(String pid, String sub) =>
      getList('/projects/$pid/$sub');

  Future<Map<String, dynamic>> addSub(String pid, String sub, Map<String, dynamic> data) =>
      post('/projects/$pid/$sub', data);

  Future<void> updateSub(String pid, String sub, String docId, Map<String, dynamic> data) =>
      put('/projects/$pid/$sub/$docId', data);

  Future<void> deleteSub(String pid, String sub, String docId) =>
      delete('/projects/$pid/$sub/$docId');
}
