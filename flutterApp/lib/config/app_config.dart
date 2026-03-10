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

  // IT22574718 backend module (ML + phase progress tracking).
  static const int    itBackendPort = 8091;

  static String get baseUrl => 'http://$backendHost:$backendPort';
  static String get itBaseUrl => 'http://$backendHost:$itBackendPort';
}
