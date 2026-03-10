import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class HuggingFaceService {
  static const _key = 'hf_api_key';
  static const _modelKey = 'hf_model';
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  Future<void> saveApiKey(String key) => _storage.write(key: _key, value: key);
  Future<String?> readApiKey() => _storage.read(key: _key);
  Future<void> deleteApiKey() => _storage.delete(key: _key);

  Future<void> saveModel(String model) => _storage.write(key: _modelKey, value: model);
  Future<String?> readModel() => _storage.read(key: _modelKey);
  Future<void> deleteModel() => _storage.delete(key: _modelKey);

  /// Send a simple text prompt to a HuggingFace model using the Inference API.
  /// Returns the resulting text or throws on error.
  Future<String> testPrompt(String prompt, {String model = 'MiniMaxAI/MiniMax-M2.5:novita'}) async {
    final key = await readApiKey();
    if (key == null || key.isEmpty) throw Exception('No HuggingFace API key configured');

    final uri = Uri.parse('https://api-inference.huggingface.co/models/$model');

    final body = json.encode({'inputs': prompt});

    final resp = await http.post(uri, headers: {
      'Authorization': 'Bearer $key',
      'Content-Type': 'application/json'
    }, body: body).timeout(const Duration(seconds: 20));

    if (resp.statusCode >= 200 && resp.statusCode < 300) {
      try {
        final j = json.decode(resp.body);
        // Many HF text models return either: { "generated_text": "..." }
        // or a list of tokens/objects. Fallback to string body when parsing fails.
        if (j is Map && j['generated_text'] is String) return j['generated_text'];
        if (j is List && j.isNotEmpty) {
          // sometimes returns [{"generated_text":"..."}] or arrays
          final first = j[0];
          if (first is Map && first['generated_text'] is String) return first['generated_text'];
          // other models may return a plain text string inside 'generated_text' or 'text'
        }
        // fallback: return the stringified JSON or raw text
        return resp.body.toString();
      } catch (_) {
        return resp.body.toString();
      }
    }

    throw Exception('HuggingFace request failed (${resp.statusCode}): ${resp.body}');
  }
}
