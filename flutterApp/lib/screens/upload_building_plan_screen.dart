import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image/image.dart' as img;
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;
import 'package:permission_handler/permission_handler.dart';

import 'package:provider/provider.dart';

import '../config/app_config.dart' as config;
import '../providers/gemini_provider.dart';
import '../services/finishing_api_prompt.dart';
import '../services/foundation_api_prompt.dart';
import '../services/gemini_api_prompt.dart';
import '../services/gemini_service.dart';
import '../services/mongo_api_service.dart';
import '../utils/constants.dart';
import 'projects/projects_screen.dart';

class UploadBuildingPlanScreen extends StatefulWidget {
  final String projectId;

  const UploadBuildingPlanScreen({super.key, required this.projectId});

  @override
  State<UploadBuildingPlanScreen> createState() =>
      _UploadBuildingPlanScreenState();
}

class _UploadBuildingPlanScreenState extends State<UploadBuildingPlanScreen> {
  static const int _maxGeminiImages = 4;
  static const int _maxGeminiImageWidth = 1400;
  static const int _geminiJpegQuality = 72;

  final _picker = ImagePicker();
  final List<XFile> _images = [];
  bool _loading = false;
  String _status = '';

  // Pipeline steps:
  //   0 = upload (pick images)
  //   1 = contour applied
  //   2 = walling extracted
  //   3 = structural frame extracted
  //   4 = saved (success)
  int _pipelineStep = 0;

  List<Uint8List> _contourResultBytes = [];

  Map<String, dynamic>? _wallingResult;
  Map<String, dynamic>? _sfResult;
  String _wallingRawText = '';
  List<Map<String, dynamic>> _encodedImages = [];
  String _savedModel = '';
  Uri? _geminiUri;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<GeminiProvider>(context, listen: false).loadKey();
    });
  }

  // â”€â”€â”€ Permissions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  Future<bool> _requestMediaPermission() async {
    if (kIsWeb) return true;

    final status = await Permission.photos.request();
    if (status.isGranted) return true;

    final storage = await Permission.storage.request();
    if (storage.isGranted) return true;

    if (status.isPermanentlyDenied || storage.isPermanentlyDenied) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
                'Photo access denied. Please enable it in app settings.'),
            action: SnackBarAction(
              label: 'Settings',
              onPressed: openAppSettings,
            ),
          ),
        );
      }
      return false;
    }
    return false;
  }

  // â”€â”€â”€ Pick Images â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  Future<void> _pickImages() async {
    final granted = await _requestMediaPermission();
    if (!granted) return;

    final picked = await _picker.pickMultiImage(imageQuality: 85);
    if (picked.isEmpty) return;

    setState(() {
      for (final img in picked) {
        if (!_images.any((e) => e.path == img.path)) {
          _images.add(img);
        }
      }
    });
  }

  void _removeImage(int index) {
    setState(() {
      _images.removeAt(index);
    });
  }

  // â”€â”€â”€ Step 1 â€” Contour Detection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  Future<void> _applyContourDetection() async {
    if (_images.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select images first.')),
      );
      return;
    }

    setState(() {
      _loading = true;
      _contourResultBytes = [];
      _status = 'Applying contour detectionâ€¦';
    });

    try {
      for (int i = 0; i < _images.length; i++) {
        final image = _images[i];
        setState(() => _status = 'Contour: processing ${image.name} (${i + 1}/${_images.length})â€¦');

        final bytes = await image.readAsBytes();
        final uri = Uri.parse('${config.AppConfig.baseUrl}/contour/detect');
        final request = http.MultipartRequest('POST', uri)
          ..files.add(http.MultipartFile.fromBytes('image', bytes, filename: image.name));

        final streamed = await request.send().timeout(const Duration(seconds: 60));
        final response = await http.Response.fromStream(streamed);

        if (response.statusCode == 200) {
          final data = json.decode(response.body) as Map<String, dynamic>;
          if (data['success'] == true) {
            final b64 = data['processed_image'] as String?;
            if (b64 == null || b64.isEmpty) throw Exception('Contour returned no image for ${image.name}');
            _contourResultBytes.add(base64Decode(b64));
          } else {
            throw Exception(data['error'] ?? 'Contour detection failed');
          }
        } else {
          throw Exception('Contour server error ${response.statusCode}');
        }
      }

      setState(() {
        _pipelineStep = 1;
        _status = '';
      });
    } on SocketException {
      _showError('Cannot reach backend. Make sure it is running on ${config.AppConfig.baseUrl}.');
    } catch (e) {
      _showError('Contour detection error: $e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  // â”€â”€â”€ Step 3 â€” Send Hough Images to Gemini â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  Future<void> _sendToGemini() async {
    setState(() {
      _loading = true;
      _status = 'Preparing contour images for Gemini...';
    });

    try {
      final geminiService = GeminiService();
      final apiKey = await geminiService.readApiKey();
      if (apiKey == null || apiKey.isEmpty) {
        throw Exception('No Gemini API key found. Please add it in Settings first.');
      }

      final selectedImages = _selectGeminiImages(_contourResultBytes);
      final imageParts = <Map<String, dynamic>>[];
      for (int i = 0; i < selectedImages.length; i++) {
        setState(() => _status = 'Preparing image ${i + 1}/${selectedImages.length} for Gemini...');
        final optimizedBytes = _optimizeGeminiImage(selectedImages[i]);
        imageParts.add({
          'inline_data': {'mime_type': 'image/jpeg', 'data': base64Encode(optimizedBytes)}
        });
      }
      _encodedImages = imageParts;

      if (!mounted) return;
      final savedModel = Provider.of<GeminiProvider>(context, listen: false).savedModel;
      _savedModel = (savedModel != null && savedModel.isNotEmpty) ? savedModel : 'gemini-2.0-flash';

      setState(() => _status = 'Extracting wall measurements with Gemini...');
      final result = await geminiService.generateContent(
        preferredModel: _savedModel,
        contents: [
          {
            'parts': [
              {'text': GeminiApiPrompt.prompt},
              ..._encodedImages,
            ]
          }
        ],
        generationConfig: {'responseMimeType': 'application/json', 'temperature': 0.2},
        timeout: const Duration(seconds: 120),
      );

      final candidateText = result.text;
      _savedModel = result.model;
      _geminiUri = Uri.parse(
        'https://generativelanguage.googleapis.com/v1beta/models/${result.model}:generateContent?key=$apiKey',
      );

      _wallingRawText = candidateText;
      _wallingResult = json.decode(_stripMarkdownJson(candidateText)) as Map<String, dynamic>;

      if (!mounted) return;
      setState(() {
        _pipelineStep = 2;
        _status = '';
      });
    } catch (e) {
      if (!mounted) return;
      _showError('Gemini error: $e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  // ─── Step 4 — Structural Frame ──────────────────────────────────────────────

  Future<void> _callStructuralFrame() async {
    setState(() {
      _loading = true;
      _status = 'Extracting structural frame with Gemini…';
    });
    try {
      final result = await GeminiService().generateContent(
        preferredModel: _savedModel,
        contents: [
          {
            'role': 'user',
            'parts': [
              {'text': GeminiApiPrompt.prompt},
              ..._encodedImages,
            ],
          },
          {
            'role': 'model',
            'parts': [{'text': _wallingRawText}],
          },
          {
            'role': 'user',
            'parts': [{'text': GeminiApiPrompt.structuralFramePrompt}],
          },
        ],
        generationConfig: {'responseMimeType': 'application/json', 'temperature': 0.2},
        timeout: const Duration(seconds: 120),
      );

      final candidateText = result.text;
      _savedModel = result.model;

      _sfResult = json.decode(_stripMarkdownJson(candidateText)) as Map<String, dynamic>;

      if (!mounted) return;
      setState(() {
        _pipelineStep = 3;
        _status = '';
      });
    } catch (e) {
      if (!mounted) return;
      _showError('Structural frame error: $e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  // ─── Step 6 — Save and Complete

  Future<void> _saveAndComplete() async {
    setState(() {
      _loading = true;
      _status = 'Saving extracted dataâ€¦';
    });
    try {
      final api = MongoApiService();
      await api.loadToken();

      if (_wallingResult != null) {
        setState(() => _status = 'Saving walling dataâ€¦');
        await api.postWalling(widget.projectId, <String, dynamic>{
          'output': <String, dynamic>{
            'units': (_wallingResult!['output'] as Map?)?['units'],
            'totalWalls': (_wallingResult!['output'] as Map?)?['totalWalls'],
          },
          'groundFloor': <String, dynamic>{
            'walls': (_wallingResult!['groundFloor'] as Map?)?['walls'] ?? {},
          },
        });
      }

      setState(() => _status = 'Saving building structure...');

      if (_sfResult != null) {
        setState(() => _status = 'Saving structural frame...');
        await api.postStructuralFrame(widget.projectId, <String, dynamic>{
          'output': <String, dynamic>{
            'units': (_sfResult!['output'] as Map?)?['units'],
            'totalColumns': (_sfResult!['output'] as Map?)?['totalColumns'],
          },
          'groundFloor': <String, dynamic>{
            'columns': (_sfResult!['groundFloor'] as Map?)?['columns'] ?? {},
          },
        });
      }


      await api.postBuildingStructure(
          widget.projectId, _wallingResult ?? <String, dynamic>{});

      // Background: generate 3D views - non-fatal
      _generate3dInBackground(api);

      if (!mounted) return;
      setState(() {
        _pipelineStep = 4;
        _loading = false;
        _status = '';
      });
    } catch (e) {
      if (!mounted) return;
      _showError('Save error: $e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _showError(String message) {
    if (!mounted) return;
    setState(() => _status = '');
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        duration: const Duration(seconds: 8),
      ),
    );
  }

  void _generate3dInBackground(MongoApiService api) {
    () async {
      try {
        if (_geminiUri == null) return;
        final foundationReqBody = json.encode({
          'contents': [
            {
              'role': 'user',
              'parts': [
                {'text': GeminiApiPrompt.prompt},
                ..._encodedImages,
              ],
            },
            {'role': 'model', 'parts': [{'text': _wallingRawText}]},
            {'role': 'user', 'parts': [{'text': FoundationApiPrompt.prompt}]},
          ],
          'generationConfig': {'temperature': 0.2},
        });
        final fResp = await http
            .post(_geminiUri!,
                headers: {'Content-Type': 'application/json'},
                body: foundationReqBody)
            .timeout(const Duration(seconds: 180));
        if (fResp.statusCode >= 200 && fResp.statusCode < 300) {
          final htmlRaw =
              (((json.decode(fResp.body)['candidates'] as List?)
                          ?.firstOrNull?['content']?['parts'] as List?)
                      ?.firstOrNull?['text'] as String?) ??
                  '';
          if (htmlRaw.trim().isNotEmpty) {
            final cleanHtml = _stripHtmlFences(htmlRaw);
            await api.setThreeJsCategory(widget.projectId, 'foundation', cleanHtml);
            final finReqBody = json.encode({
              'contents': [
                {
                  'role': 'user',
                  'parts': [
                    {'text': GeminiApiPrompt.prompt},
                    ..._encodedImages,
                  ],
                },
                {'role': 'model', 'parts': [{'text': _wallingRawText}]},
                {'role': 'user', 'parts': [{'text': FoundationApiPrompt.prompt}]},
                {'role': 'model', 'parts': [{'text': cleanHtml}]},
                {'role': 'user', 'parts': [{'text': FinishingApiPrompt.prompt}]},
              ],
              'generationConfig': {'temperature': 0.2},
            });
            final finResp = await http
                .post(_geminiUri!,
                    headers: {'Content-Type': 'application/json'},
                    body: finReqBody)
                .timeout(const Duration(seconds: 240));
            if (finResp.statusCode >= 200 && finResp.statusCode < 300) {
              final finHtmlRaw =
                  (((json.decode(finResp.body)['candidates'] as List?)
                              ?.firstOrNull?['content']?['parts'] as List?)
                          ?.firstOrNull?['text'] as String?) ??
                      '';
              if (finHtmlRaw.trim().isNotEmpty) {
                await api.setThreeJsCategory(
                    widget.projectId, 'finishing', _stripHtmlFences(finHtmlRaw));
              }
            }
          }
        }
      } catch (e) {
        debugPrint('3D generation error (non-fatal): $e');
      }
    }();
  }

  String _stripHtmlFences(String raw) {
    final trimmed = raw.trim();
    final fenceMatch =
        RegExp(r'```(?:html)?\s*([\s\S]*?)```').firstMatch(trimmed);
    if (fenceMatch != null) return fenceMatch.group(1)!.trim();
    final idxDoctype = trimmed.toLowerCase().indexOf('<!doctype');
    if (idxDoctype != -1) return trimmed.substring(idxDoctype);
    final idxHtml = trimmed.toLowerCase().indexOf('<html');
    if (idxHtml != -1) return trimmed.substring(idxHtml);
    return trimmed;
  }

  String _stripMarkdownJson(String raw) {
    final trimmed = raw.trim();
    final fenceMatch =
        RegExp(r'```(?:json)?\s*([\s\S]*?)```').firstMatch(trimmed);
    if (fenceMatch != null) return fenceMatch.group(1)!.trim();
    final start = trimmed.indexOf('{');
    final end = trimmed.lastIndexOf('}');
    if (start != -1 && end != -1 && end > start) {
      return trimmed.substring(start, end + 1);
    }
    return trimmed;
  }

  List<Uint8List> _selectGeminiImages(List<Uint8List> images) {
    if (images.length <= _maxGeminiImages) return List<Uint8List>.from(images);

    final selected = <Uint8List>[];
    for (int i = 0; i < _maxGeminiImages; i++) {
      final index = (i * (images.length - 1) / (_maxGeminiImages - 1)).round();
      selected.add(images[index]);
    }
    return selected;
  }

  Uint8List _optimizeGeminiImage(Uint8List originalBytes) {
    final decoded = img.decodeImage(originalBytes);
    if (decoded == null) return originalBytes;

    img.Image optimized = decoded;
    if (decoded.width > _maxGeminiImageWidth) {
      optimized = img.copyResize(decoded, width: _maxGeminiImageWidth);
    }

    return Uint8List.fromList(
      img.encodeJpg(optimized, quality: _geminiJpegQuality),
    );
  }

  // â”€â”€â”€ Loading View â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  Widget _buildLoadingView() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const CircularProgressIndicator(color: AppColors.primary),
            const SizedBox(height: 24),
            Text(
              _status,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 15,
                color: AppColors.primary,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // â”€â”€â”€ Build â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  @override
  Widget build(BuildContext context) {
    if (_loading) return Scaffold(appBar: _buildAppBar(), body: _buildLoadingView());

    return Scaffold(
      appBar: _buildAppBar(),
      body: switch (_pipelineStep) {
        0 => _buildUploadView(),
        1 => _buildContourResultView(),
        2 => _buildAnalysisResultView(
              step: 2,
              label: 'Walling Measurements',
              icon: Icons.crop_square_outlined,
              color: const Color(0xFF6A1B9A),
              result: _wallingResult,
              nextLabel: 'Continue - Structural Frame',
              onNext: _callStructuralFrame,
            ),
        3 => _buildAnalysisResultView(
              step: 3,
              label: 'Structural Frame',
              icon: Icons.account_tree_outlined,
              color: const Color(0xFF1565C0),
              result: _sfResult,
              nextLabel: 'Save & Complete',
              onNext: _saveAndComplete,
            ),
        4 => _buildSuccessView(),
        _ => _buildUploadView(),
      },
    );
  }

  AppBar _buildAppBar() => AppBar(
        title: const Text('Upload Building Plans'),
        backgroundColor: AppColors.primary,
      );

  // â”€â”€â”€ Step 0 â€” Upload View â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  Widget _buildUploadView() {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const _PipelineProgress(currentStep: 0),
          const SizedBox(height: 16),
          Card(
            color: AppColors.primary.withAlpha(20),
            child: const Padding(
              padding: EdgeInsets.all(12.0),
              child: Row(
                children: [
                  Icon(Icons.info_outline, color: AppColors.primary),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Upload building plan images. They will be processed with '
                      'Contour Detection, then sent to '
                      'Gemini AI to extract walling measurements.',
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: _pickImages,
            icon: const Icon(Icons.add_photo_alternate_outlined),
            label: const Text('Select Images'),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 14),
              side: const BorderSide(color: AppColors.primary),
              foregroundColor: AppColors.primary,
            ),
          ),
          const SizedBox(height: 12),
          if (_images.isNotEmpty) ...[
            Text(
              '${_images.length} image(s) selected',
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            SizedBox(
              height: 110,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: _images.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (ctx, i) => _ImageThumb(
                  file: _images[i],
                  onRemove: () => _removeImage(i),
                ),
              ),
            ),
            const SizedBox(height: 16),
          ],
          const Spacer(),
          ElevatedButton.icon(
            onPressed: _images.isEmpty ? null : _applyContourDetection,
            icon: const Icon(Icons.polyline_outlined),
            label: const Text(
              'Start â€” Apply Contour Detection',
              style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
            ),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
          ),
          const SizedBox(height: 8),
          TextButton(
            onPressed: () => Navigator.pushReplacement(
              context,
              MaterialPageRoute(builder: (_) => const ProjectsScreen()),
            ),
            child: const Text('Skip for now'),
          ),
        ],
      ),
    );
  }

  // â”€â”€â”€ Step 1 â€” Contour Result View â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  Widget _buildContourResultView() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const _PipelineProgress(currentStep: 1),
          const SizedBox(height: 12),
          Row(
            children: [
              const Icon(Icons.check_circle, color: Color(0xFF2E7D32), size: 20),
              const SizedBox(width: 8),
              Text(
                'Contour Detection complete â€” ${_contourResultBytes.length} image(s)',
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Expanded(
            child: ListView.separated(
              itemCount: _contourResultBytes.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (ctx, i) => _CVResultCard(
                label: 'Contour result â€” image ${i + 1}',
                imageBytes: _contourResultBytes[i],
                color: const Color(0xFF2E7D32),
              ),
            ),
          ),
          const SizedBox(height: 12),
          ElevatedButton.icon(
            onPressed: _sendToGemini,
            icon: const Icon(Icons.auto_awesome),
            label: const Text(
              'Send to Gemini - Extract Measurements',
              style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
            ),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF6A1B9A),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
          ),
        ],
      ),
    );
  }

  // â”€â”€â”€ Step 3 â€” Gemini Walling Result View â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  Widget _buildAnalysisResultView({
    required int step,
    required String label,
    required IconData icon,
    required Color color,
    required Map<String, dynamic>? result,
    required String nextLabel,
    required VoidCallback onNext,
  }) {
    final prettyJson = const JsonEncoder.withIndent('  ').convert(result ?? {});

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _PipelineProgress(currentStep: step),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          color: color.withAlpha(20),
          child: Row(
            children: [
              Icon(icon, color: color, size: 20),
              const SizedBox(width: 8),
              Text(
                label,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
            ],
          ),
        ),
        Expanded(
          child: Container(
            margin: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFF0D1117),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: color.withAlpha(60)),
            ),
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(14),
              child: SelectableText(
                prettyJson,
                style: const TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 11.5,
                  color: Color(0xFF79C0FF),
                  height: 1.5,
                ),
              ),
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 0, 12, 16),
          child: ElevatedButton.icon(
            onPressed: onNext,
            icon: Icon(step < 4 ? Icons.arrow_forward : Icons.save_outlined),
            label: Text(
              nextLabel,
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
            ),
            style: ElevatedButton.styleFrom(
              backgroundColor: color,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10)),
            ),
          ),
        ),
      ],
    );
  }

  // â”€â”€â”€ Step 4 â€” Success View â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  Widget _buildSuccessView() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: const Color(0xFF2E7D32).withAlpha(20),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.check_circle_rounded,
                color: Color(0xFF2E7D32),
                size: 80,
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              'Successfully extracted all data',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: Color(0xFF2E7D32),
              ),
            ),
            const SizedBox(height: 12),
            const Text(
              'Walling, structural frame, finishing data and building structure have been saved to your project.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, color: Colors.grey),
            ),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: () => Navigator.pushReplacement(
                context,
                MaterialPageRoute(builder: (_) => const ProjectsScreen()),
              ),
              icon: const Icon(Icons.folder_open),
              label: const Text(
                'Go to Projects',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                padding:
                    const EdgeInsets.symmetric(horizontal: 32, vertical: 14),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// â”€â”€â”€ Pipeline Progress Indicator â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class _PipelineProgress extends StatelessWidget {
  final int currentStep; // 0–6

  const _PipelineProgress({required this.currentStep});

  @override
  Widget build(BuildContext context) {
    const steps = ['Upload', 'Contour', 'Walls', 'Frame', 'Done'];
    const colors = [
      AppColors.primary,
      Color(0xFF2E7D32),
      Color(0xFF6A1B9A),
      Color(0xFF1565C0),
      Color(0xFF2E7D32),
    ];

    return Row(
      children: List.generate(steps.length, (i) {
        final active = i <= currentStep;
        final color = active ? colors[i] : Colors.grey.shade300;
        return Expanded(
          child: Column(
            children: [
              Container(
                height: 6,
                margin: EdgeInsets.only(right: i < steps.length - 1 ? 4 : 0),
                decoration: BoxDecoration(
                  color: color,
                  borderRadius: BorderRadius.circular(3),
                ),
              ),
              const SizedBox(height: 4),
              Text(
                steps[i],
                style: TextStyle(
                  fontSize: 10,
                  color: active ? colors[i] : Colors.grey,
                  fontWeight:
                      i == currentStep ? FontWeight.bold : FontWeight.normal,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        );
      }),
    );
  }
}

// â”€â”€â”€ CV Result Card â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class _CVResultCard extends StatelessWidget {
  final String label;
  final Uint8List imageBytes;
  final Color color;

  const _CVResultCard({
    required this.label,
    required this.imageBytes,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: BorderSide(color: color.withAlpha(60)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 10, 12, 6),
            child: Text(
              label,
              style: TextStyle(
                  fontWeight: FontWeight.w600, color: color, fontSize: 13),
            ),
          ),
          ClipRRect(
            borderRadius:
                const BorderRadius.vertical(bottom: Radius.circular(10)),
            child: Image.memory(
              imageBytes,
              width: double.infinity,
              fit: BoxFit.fitWidth,
            ),
          ),
        ],
      ),
    );
  }
}

// â”€â”€â”€ Thumbnail widget â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class _ImageThumb extends StatelessWidget {
  final XFile file;
  final VoidCallback onRemove;

  const _ImageThumb({required this.file, required this.onRemove});

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: kIsWeb
              ? Image.network(file.path,
                  width: 100, height: 100, fit: BoxFit.cover)
              : Image.file(File(file.path),
                  width: 100, height: 100, fit: BoxFit.cover),
        ),
        Positioned(
          top: 2,
          right: 2,
          child: GestureDetector(
            onTap: onRemove,
            child: Container(
              decoration: const BoxDecoration(
                color: Colors.black54,
                shape: BoxShape.circle,
              ),
              padding: const EdgeInsets.all(2),
              child: const Icon(Icons.close, color: Colors.white, size: 16),
            ),
          ),
        ),
      ],
    );
  }
}

