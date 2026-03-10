import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class OpenAIService {
  static const _key = 'openai_api_key';
  static const _modelKey = 'openai_model';
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  Future<void> saveApiKey(String key) => _storage.write(key: _key, value: key);
  Future<String?> readApiKey() => _storage.read(key: _key);
  Future<void> deleteApiKey() => _storage.delete(key: _key);

  Future<void> saveModel(String model) => _storage.write(key: _modelKey, value: model);
  Future<String?> readModel() => _storage.read(key: _modelKey);
  Future<void> deleteModel() => _storage.delete(key: _modelKey);

  /// Simple Responses API call using the stored key. Returns text or throws.
  Future<String> testPrompt(String prompt, {String model = 'gpt-5.2'}) async {
    final key = await readApiKey();
    if (key == null || key.isEmpty) throw Exception('No OpenAI API key configured');

    final uri = Uri.parse('https://api.openai.com/v1/responses');
    final body = json.encode({
      'model': model,
      'input': prompt,
      'max_output_tokens': 200
    });

    final resp = await http.post(uri, headers: {
      'Authorization': 'Bearer $key',
      'Content-Type': 'application/json'
    }, body: body).timeout(const Duration(seconds: 20));

    if (resp.statusCode >= 200 && resp.statusCode < 300) {
      try {
        final j = json.decode(resp.body);
        // Prefer 'output_text' if available
        if (j is Map && j['output_text'] is String && (j['output_text'] as String).isNotEmpty) return j['output_text'];
        // Older/alternate shape: 'output' list with 'content' parts
        if (j is Map && j['output'] is List && j['output'].isNotEmpty) {
          final out = j['output'][0];
          if (out is Map && out['content'] is List && out['content'].isNotEmpty) {
            final first = out['content'][0];
            if (first is Map && first['text'] is String) return first['text'];
          }
        }
        return resp.body.toString();
      } catch (_) {
        return resp.body.toString();
      }
    }

    throw Exception('OpenAI request failed (${resp.statusCode}): ${resp.body}');
  }
}
