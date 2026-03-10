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
      try {
        return jsonDecode(res.body) as List<dynamic>;
      } on FormatException {
        throw Exception(_unexpectedResponseMessage(res));
      }
    }
    try {
      final err = jsonDecode(res.body);
      throw Exception(err['error'] ?? 'HTTP ${res.statusCode}');
    } on FormatException {
      throw Exception(_unexpectedResponseMessage(res));
    }
  }

  Map<String, dynamic> _parse(http.Response res) {
    try {
      final body = jsonDecode(res.body);
      if (res.statusCode >= 200 && res.statusCode < 300) {
        return body as Map<String, dynamic>;
      }
      throw Exception((body as Map)['error'] ?? 'HTTP ${res.statusCode}');
    } on FormatException {
      throw Exception(_unexpectedResponseMessage(res));
    }
  }

  String _unexpectedResponseMessage(http.Response res) {
    final snippet = res.body.replaceAll(RegExp(r'\s+'), ' ').trim();
    final preview = snippet.length > 120 ? '${snippet.substring(0, 120)}...' : snippet;
    return 'Unexpected response from ${res.request?.url ?? 'server'} '
        '(HTTP ${res.statusCode}). Check that the app is pointing to ${AppConfig.baseUrl}. '
        'Response: $preview';
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

  Future<Map<String, dynamic>> postBuildingStructure(
          String pid, Map<String, dynamic> structureData) =>
      post('/buildingstructure/$pid', structureData);

  Future<Map<String, dynamic>> getBuildingStructure(String pid) =>
      get('/buildingstructure/$pid');

  Future<Map<String, dynamic>> postStructuralFrame(
          String pid, Map<String, dynamic> data) =>
      post('/structuralframe/$pid', data);

  Future<Map<String, dynamic>> getStructuralFrame(String pid) =>
      get('/structuralframe/$pid');

  Future<Map<String, dynamic>> postWalling(
          String pid, Map<String, dynamic> data) =>
      post('/walling/$pid', data);

  Future<Map<String, dynamic>> getWalling(String pid) =>
      get('/walling/$pid');

  Future<Map<String, dynamic>> postFinishing(
          String pid, Map<String, dynamic> data) =>
      post('/finishing/$pid', data);

  Future<Map<String, dynamic>> getFinishing(String pid) =>
      get('/finishing/$pid');

  // ─── Subcollection endpoints ───────────────────────────────────────────────
  Future<List<dynamic>> getSub(String pid, String sub) =>
      getList('/projects/$pid/$sub');

  Future<Map<String, dynamic>> addSub(String pid, String sub, Map<String, dynamic> data) =>
      post('/projects/$pid/$sub', data);

  Future<void> updateSub(String pid, String sub, String docId, Map<String, dynamic> data) =>
      put('/projects/$pid/$sub/$docId', data);

  Future<void> deleteSub(String pid, String sub, String docId) =>
      delete('/projects/$pid/$sub/$docId');

  // ─── ThreeJS endpoints ─────────────────────────────────────────────────────
  Future<Map<String, dynamic>> getThreeJs(String pid) => get('/threejs/$pid');

  Future<String?> getThreeJsCategory(String pid, String category) async {
    final res = await get('/threejs/$pid/$category');
    return res['html_code'] as String?;
  }

  Future<void> setThreeJsCategory(String pid, String category, String htmlCode) =>
      post('/threejs/$pid/$category', {'html_code': htmlCode});

  // ─── Materials library ─────────────────────────────────────────────────────

  /// All materials sorted by name. Returns List of {_id, name, brands, sizes}.
  Future<List<dynamic>> getAllMaterials() => getList('/materials');

  /// Create a material. Returns the created doc.
  Future<Map<String, dynamic>> createMaterial(
      String name, List<String> brands, List<String> sizes) =>
      post('/materials', {'name': name, 'brands': brands, 'sizes': sizes});

  /// Update brands/sizes (and optionally name) for a material by id.
  Future<Map<String, dynamic>> updateMaterial(
      String id, {String? name, List<String>? brands, List<String>? sizes}) {
    final body = <String, dynamic>{};
    if (name   != null) body['name']   = name;
    if (brands != null) body['brands'] = brands;
    if (sizes  != null) body['sizes']  = sizes;
    return put('/materials/$id', body);
  }

  /// Delete a material by id.
  Future<void> deleteMaterial(String id) => delete('/materials/$id');

  /// Brands + sizes for a material name (used by _MatRow select buttons).
  Future<Map<String, dynamic>> getMaterialOptions(String materialName) =>
      get('/materials/options/${Uri.encodeComponent(materialName)}');
}
