import 'package:flutter/foundation.dart';
import '../services/hf_service.dart';

class HfProvider extends ChangeNotifier {
  final HuggingFaceService _svc = HuggingFaceService();
  String? _apiKey;
  String? _savedModel;
  bool _loading = false;

  String? get apiKey => _apiKey;
  String? get savedModel => _savedModel;
  bool get loading => _loading;

  Future<void> loadKey() async {
    _loading = true;
    notifyListeners();
    _apiKey = await _svc.readApiKey();
    _savedModel = await _svc.readModel();
    _loading = false;
    notifyListeners();
  }

  Future<void> saveKey(String key) async {
    _loading = true;
    notifyListeners();
    await _svc.saveApiKey(key);
    _apiKey = key;
    _loading = false;
    notifyListeners();
  }

  Future<void> clearKey() async {
    _loading = true;
    notifyListeners();
    await _svc.deleteApiKey();
    _apiKey = null;
    _loading = false;
    notifyListeners();
  }

  Future<void> saveModelName(String model) async {
    await _svc.saveModel(model);
    _savedModel = model;
    notifyListeners();
  }

  Future<void> clearModelName() async {
    await _svc.deleteModel();
    _savedModel = null;
    notifyListeners();
  }

  Future<String> testPrompt(String prompt, {String model = 'MiniMaxAI/MiniMax-M2.5:novita'}) async {
    return _svc.testPrompt(prompt, model: model);
  }
}
