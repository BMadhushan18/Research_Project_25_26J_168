// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter_test/flutter_test.dart';

import 'package:material_estimate/app.dart';
import 'package:material_estimate/core/services/api_client.dart';
import 'package:material_estimate/core/models/health_status.dart';

class TestApiClient extends ApiClient {
  TestApiClient() : super();

  @override
  Future<void> hydrate() async {
    // No-op for tests
    return;
  }

  @override
  bool get isReady => true;

  @override
  String get baseUrl => 'http://localhost:8001';

  @override
  Future<HealthStatus> fetchHealth() async => HealthStatus.fromJson({'available': false});
}

void main() {
  testWidgets('Voice UI smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame using a test ApiClient that doesn't require SharedPreferences/network.
    await tester.pumpWidget(SmartLogisticsApp(apiClient: TestApiClient()));

    // Verify navigation labels are present
    expect(find.text('Predict'), findsOneWidget);
    expect(find.text('Train'), findsOneWidget);
  });
}
