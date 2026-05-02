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
  String _itUrl(String path) => '${AppConfig.itBaseUrl}$path';

  Future<Map<String, dynamic>> get(String path) async {
    await _ensureToken();
    final res = await http
        .get(Uri.parse(_url(path)), headers: _headers)
        .timeout(const Duration(seconds: 15));
    return _parse(res);
  }

  Future<Map<String, dynamic>> post(String path,Map<String, dynamic> body,) async {
    await _ensureToken();
    final res = await http
        .post(
          Uri.parse(_url(path)),
          headers: _headers,
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 15));
    return _parse(res);
  }

  Future<Map<String, dynamic>> postAbsolute(String absoluteUrl,Map<String, dynamic> body,) async {
    await _ensureToken();
    final res = await http
        .post(
          Uri.parse(absoluteUrl),
          headers: _headers,
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 15));
    return _parse(res);
  }

  Future<List<dynamic>> getListAbsolute(String absoluteUrl) async {
    await _ensureToken();
    final res = await http
        .get(Uri.parse(absoluteUrl), headers: _headers)
        .timeout(const Duration(seconds: 15));

    if (res.statusCode >= 200 && res.statusCode < 300) {
      return jsonDecode(res.body) as List<dynamic>;
    }

    final decoded = _tryDecodeJson(res.body);
    if (decoded is Map && decoded['error'] != null) {
      throw Exception(decoded['error']);
    }

    final preview = res.body.replaceAll(RegExp(r'\s+'), ' ').trim();
    final snippet =
        preview.length > 120 ? '${preview.substring(0, 120)}...' : preview;
    throw Exception(
      'HTTP ${res.statusCode}: non-JSON response from ${res.request?.url}. '
      'Check AppConfig base URLs/ports. Response: $snippet',
    );
  }

  Future<Map<String, dynamic>> getAbsolute(String absoluteUrl) async {
    await _ensureToken();
    final res = await http
        .get(Uri.parse(absoluteUrl), headers: _headers)
        .timeout(const Duration(seconds: 15));
    return _parse(res);
  }

  Future<Map<String, dynamic>> put(
    String path,
    Map<String, dynamic> body,
  ) async {
    await _ensureToken();
    final res = await http
        .put(
          Uri.parse(_url(path)),
          headers: _headers,
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 15));
    return _parse(res);
  }

  Future<Map<String, dynamic>> delete(String path) async {
    await _ensureToken();
    final res = await http
        .delete(Uri.parse(_url(path)), headers: _headers)
        .timeout(const Duration(seconds: 15));
    return _parse(res);
  }

  Future<List<dynamic>> getList(String path) async {
    await _ensureToken();
    final res = await http
        .get(Uri.parse(_url(path)), headers: _headers)
        .timeout(const Duration(seconds: 15));

    if (res.statusCode >= 200 && res.statusCode < 300) {
      return jsonDecode(res.body) as List<dynamic>;
    }

    final err = jsonDecode(res.body);
    throw Exception(err['error'] ?? 'HTTP ${res.statusCode}');
  }

  Map<String, dynamic> _parse(http.Response res) {
    final decoded = _tryDecodeJson(res.body);

    if (res.statusCode >= 200 && res.statusCode < 300) {
      if (decoded is Map<String, dynamic>) return decoded;
      if (decoded != null) return {'data': decoded};
      return {
        'data': res.body,
      };
    }

    if (decoded is Map && decoded['error'] != null) {
      throw Exception(decoded['error']);
    }

    final preview = res.body.replaceAll(RegExp(r'\s+'), ' ').trim();
    final snippet =
        preview.length > 120 ? '${preview.substring(0, 120)}...' : preview;

    throw Exception(
      'HTTP ${res.statusCode}: non-JSON response from ${res.request?.url}. '
      'Check AppConfig.baseUrl/port. Response: $snippet',
    );
  }

  dynamic _tryDecodeJson(String body) {
    try {
      return jsonDecode(body);
    } catch (_) {
      return null;
    }
  }

  // ─── Auth endpoints ────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> signup(
    String email,
    String password,
    String displayName,
  ) async {
    final res = await post('/auth/signup', {
      'email': email,
      'password': password,
      'displayName': displayName,
    });
    await saveToken(res['token'] as String);
    return res['user'] as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> signin(String email, String password) async {
    final res = await post('/auth/signin', {
      'email': email,
      'password': password,
    });
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

  Future<Map<String, dynamic>> addSub(
    String pid,
    String sub,
    Map<String, dynamic> data,
  ) =>
      post('/projects/$pid/$sub', data);

  Future<void> updateSub(
    String pid,
    String sub,
    String docId,
    Map<String, dynamic> data,
  ) =>
      put('/projects/$pid/$sub/$docId', data);

  Future<void> deleteSub(String pid, String sub, String docId) =>
      delete('/projects/$pid/$sub/$docId');

  //######################### IT22574718 #######################################################

  Future<Map<String, dynamic>> predictFoundationDuration(
    Map<String, dynamic> payload,
  ) {
    return postAbsolute(_itUrl('/ml/predict-foundation'), payload);
  }

  Future<Map<String, dynamic>> predictWallDuration(
    Map<String, dynamic> payload,
  ) {
    return postAbsolute(_itUrl('/ml/predict-wall'), payload);
  }

  Future<Map<String, dynamic>> predictRoofDuration(
    Map<String, dynamic> payload,
  ) {
    return postAbsolute(_itUrl('/ml/predict-roof'), payload);
  }

  Future<Map<String, dynamic>> predictDoorWindowDuration(
    Map<String, dynamic> payload,
  ) {
    return postAbsolute(_itUrl('/ml/predict-door-window'), payload);
  }

  Future<Map<String, dynamic>> predictPlasteringDuration(
    Map<String, dynamic> payload,
  ) {
    return postAbsolute(_itUrl('/ml/predict-plastering'), payload);
  }

  Future<Map<String, dynamic>> predictFlooringDuration(
    Map<String, dynamic> payload,
  ) {
    return postAbsolute(_itUrl('/ml/predict-flooring'), payload);
  }

  Future<Map<String, dynamic>> predictPaintingDuration(
    Map<String, dynamic> payload,
  ) {
    return postAbsolute(_itUrl('/ml/predict-painting'), payload);
  }

  /// Save a phase duration row
  Future<Map<String, dynamic>> savePhaseDuration({
    required String pid,
    required String phaseId,
    required String phaseName,
    required int durationDays,
    required int laborCount,
  }) {
    return postAbsolute(_itUrl('/phase-durations/save'), {
      "pid": pid,
      "phaseId": phaseId,
      "phaseName": phaseName,
      "durationDays": durationDays,
      "laborCount": laborCount,
    });
  }

  Future<Map<String, dynamic>> savePhaseDurationPayload(
    Map<String, dynamic> payload,
  ) {
    return postAbsolute(_itUrl('/phase-durations/save'), payload);
  }

  Future<Map<String, dynamic>> savePhaseDailyLogPayload(
    Map<String, dynamic> payload,
  ) {
    return postAbsolute(_itUrl('/phase-daily-logs/save'), payload);
  }

  Future<List<dynamic>> getRecentPhaseDailyLogs(
    String pid,
    String phaseId, {
    int limit = 7,
  }) {
    final normalizedLimit = limit < 1 ? 1 : limit;
    return getListAbsolute(
      _itUrl('/phase-daily-logs/recent/$pid/$phaseId?limit=$normalizedLimit'),
    );
  }

  /// For calendar view - get more logs
  Future<List<dynamic>> getPhaseDailyLogs(
    String pid,
    String phaseId, {
    int limit = 365,
  }) {
    final normalizedLimit = limit < 1 ? 1 : limit;
    return getListAbsolute(
      _itUrl('/phase-daily-logs/recent/$pid/$phaseId?limit=$normalizedLimit'),
    );
  }

  Future<int> getCompletedPhaseDays(String pid, String phaseId) async {
    final res = await getAbsolute(
      _itUrl('/phase-daily-logs/completed-days/$pid/$phaseId'),
    );
    final value = res['completedDays'];
    if (value is int) return value;
    if (value is num) return value.toInt();
    return int.tryParse('${value ?? ''}') ?? 0;
  }

  Future<Map<String, dynamic>> completePhaseDuration({
    required String pid,
    required String phaseId,
    required String actualCompletedDate,
  }) {
    return postAbsolute(_itUrl('/phase-durations/complete'), {
      'pid': pid,
      'phaseId': phaseId,
      'actualCompletedDate': actualCompletedDate,
    });
  }

  Future<Map<String, dynamic>> savePhaseDailyLog({
    required String pid,
    required String phaseId,
    required String phaseName,
    required String logDate,
    required bool workedToday,
    required int laborCount,
    required String? workType,
    required int hoursPerLabor,
    required int dailyManHours,
    String? skipReason,
  }) {
    return postAbsolute(_itUrl('/phase-daily-logs/save'), {
      'pid': pid,
      'phaseId': phaseId,
      'phaseName': phaseName,
      'logDate': logDate,
      'workedToday': workedToday,
      'laborCount': laborCount,
      'workType': workType,
      'hoursPerLabor': hoursPerLabor,
      'dailyManHours': dailyManHours,
      'skipReason': skipReason,
    });
  }

  Future<List<dynamic>> getPhaseDurations(String pid) {
    return getListAbsolute(_itUrl('/phase-durations/$pid'));
  }

  Future<double> getBoqReportGrandTotal(String pid) async {
    final res = await getAbsolute(_itUrl('/boq-report/grand-total/$pid'));
    final value = res['grandTotal'];
    if (value is num) return value.toDouble();
    return double.tryParse('${value ?? ''}') ?? 0.0;
  }

  Future<Map<String, double>> getBoqPredictionCosts(String pid) async {
    final res = await getAbsolute(_itUrl('/boq-predictions/costs/$pid'));

    double toDouble(dynamic value) {
      if (value is num) return value.toDouble();
      return double.tryParse('${value ?? ''}') ?? 0.0;
    }

    return {
      'labor_cost_lkr': toDouble(
        res['labor_cost_lkr'] ?? res['labour_cost_lkr'] ?? res['total_labour_cost_rs'],
      ),
      'machinery_cost_lkr': toDouble(
        res['machinery_cost_lkr'] ?? res['total_machinery_cost_rs'],
      ),
      'vehicle_cost_lkr': toDouble(
        res['vehicle_cost_lkr'] ?? res['total_vehicle_cost_rs'],
      ),
    };
  }

  //######################### IT22574718#######################################################
}