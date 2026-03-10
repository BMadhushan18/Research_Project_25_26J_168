import 'package:flutter/foundation.dart';

/// Switch between Firebase and MongoDB backends.
/// kUseMongo = true  → MongoDB REST backend (active)
/// kUseMongo = false → Firebase/Firestore (disabled but code preserved)
class AppConfig {
  AppConfig._();

  static const bool kUseMongo = true;

  /// PC's local WiFi IP — Android device must be on the same network.
  static const String backendHost = '192.168.8.103';
  // Core Mongo backend (auth/projects/subcollections).
  static const int    backendPort = 8090;
  /// Optional overrides:
  /// flutter run --dart-define=BACKEND_HOST=192.168.x.x --dart-define=BACKEND_PORT=8090
  static const String _backendHostOverride =
      String.fromEnvironment('BACKEND_HOST', defaultValue: '');
  static const int backendPort =
      int.fromEnvironment('BACKEND_PORT', defaultValue: 8090);

  /// PC's LAN IP — keep this in sync with the machine running app.py.
  /// For Android emulator use 10.0.2.2; for a real device use the PC's WiFi IP.
  static const String _lanIp = '192.168.8.103';

  static String get backendHost {
    if (_backendHostOverride.isNotEmpty) return _backendHostOverride;

    if (kIsWeb) return '127.0.0.1';

    // Real Android device on the same WiFi — use the PC's LAN IP directly.
    if (defaultTargetPlatform == TargetPlatform.android) {
      return _lanIp;
    }

    // Windows / Linux / macOS desktop and iOS simulator
    return '127.0.0.1';
  }

  // IT22574718 backend module (ML + phase progress tracking).
  static const int    itBackendPort = 8091;

  static String get baseUrl => 'http://$backendHost:$backendPort';
  static String get itBaseUrl => 'http://$backendHost:$itBackendPort';
}
