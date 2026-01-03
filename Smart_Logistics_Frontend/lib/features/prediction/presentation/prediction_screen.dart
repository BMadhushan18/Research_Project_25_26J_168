import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:file_selector/file_selector.dart';

import '../../../core/models/prediction_models.dart';
import '../../../core/services/api_client.dart';

/// Modern prediction screen with Material Design 3
class PredictionScreen extends StatefulWidget {
  const PredictionScreen({super.key});

  @override
  State<PredictionScreen> createState() => _PredictionScreenState();
}

class _PredictionScreenState extends State<PredictionScreen> {
  final TextEditingController _boqController = TextEditingController();
  bool _isLoading = false;
  PredictionResponse? _prediction;
  String? _errorMessage;
  String? _selectedFileName;

  @override
  void dispose() {
    _boqController.dispose();
    super.dispose();
  }

  Future<void> _submitPrediction() async {
    if (_boqController.text.isEmpty) {
      setState(() => _errorMessage = 'Please enter BOQ text');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final apiClient = Provider.of<ApiClient>(context, listen: false);
      final request = PredictionRequest(boqText: _boqController.text);
      final response = await apiClient.predictBoq(request);

      if (mounted) {
        setState(() {
          _prediction = response;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _errorMessage = 'Error: ${e.toString()}');
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  /// Pick a file (csv, excel, pdf, docx, txt) and submit to the backend for analysis
  Future<void> _pickFileAndUpload() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _selectedFileName = null;
    });

    try {
      final apiClient = Provider.of<ApiClient>(context, listen: false);

      final XTypeGroup types = XTypeGroup(
        label: 'BOQ Files',
        extensions: ['csv', 'xls', 'xlsx', 'pdf', 'doc', 'docx', 'txt'],
      );

      final XFile? file = await openFile(acceptedTypeGroups: [types]);
      if (file == null) return; // user cancelled

      setState(() => _selectedFileName = file.name);

      final response = await apiClient.predictFromFile(file);

      if (mounted) {
        setState(() {
          _prediction = response;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _errorMessage = 'File upload failed: ${e.toString()}');
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('BOQ Analysis'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: _prediction != null
          ? _buildPredictionReport(context, colorScheme)
          : _buildInputForm(context, colorScheme),
    );
  }

  /// Build input form
  Widget _buildInputForm(BuildContext context, ColorScheme colorScheme) {
    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            /// Info card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Row(
                  children: [
                    Icon(Icons.info_outline, color: colorScheme.primary),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Enter your Bill of Quantities (BOQ) text to get material estimates and waste reduction insights.',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            /// Input label
            Text(
              'BOQ Text',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),

            /// Input field
            TextField(
              controller: _boqController,
              maxLines: 8,
              minLines: 8,
              decoration: InputDecoration(
                hintText:
                    'e.g., Supply and lay 50 m3 concrete using ACC cement and local sand...',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                filled: true,
                fillColor: colorScheme.primary.withValues(alpha: 0.05),
                errorText: _errorMessage,
              ),
            ),
            const SizedBox(height: 16),

            /// Quick presets
            Text(
              'Quick Presets',
              style: Theme.of(
                context,
              ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            _buildPresetButtons(context, colorScheme),
            const SizedBox(height: 16),

            /// File upload card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12.0),
                child: Row(
                  children: [
                    Icon(Icons.upload_file, color: colorScheme.primary),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Upload BOQ File',
                            style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Supported: .csv, .xls, .xlsx, .pdf, .doc, .docx, .txt',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                          if (_selectedFileName != null) ...[
                            const SizedBox(height: 8),
                            Text('Selected: $_selectedFileName', style: Theme.of(context).textTheme.bodySmall),
                          ],
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton.icon(
                      icon: const Icon(Icons.attach_file),
                      label: const Text('Choose & Analyze'),
                      onPressed: _isLoading ? null : _pickFileAndUpload,
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            /// Submit button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                label: Text(_isLoading ? 'Analyzing...' : 'Analyze BOQ'),
                onPressed: _isLoading ? null : _submitPrediction,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Build preset buttons
  Widget _buildPresetButtons(BuildContext context, ColorScheme colorScheme) {
    final presets = [
      ('Concrete Work', 'Supply and lay 50 m3 concrete using ACC cement'),
      ('Excavation', 'Excavate and remove 200 m3 of soil using backhoe'),
      ('Interior', 'Supply and install 200 m2 gypsum partitions'),
    ];

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: presets
          .map(
            (preset) => ActionChip(
              label: Text(preset.$1),
              onPressed: () {
                _boqController.text = preset.$2;
                setState(() => _errorMessage = null);
              },
              avatar: Icon(Icons.add, size: 18, color: colorScheme.primary),
            ),
          )
          .toList(),
    );
  }

  /// Build prediction report
  Widget _buildPredictionReport(BuildContext context, ColorScheme colorScheme) {
    final pred = _prediction!.prediction;

    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            /// Status banner
            Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [colorScheme.primary, colorScheme.secondary],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(12),
              ),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.check_circle, color: Colors.white),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'Analysis Complete',
                          style: Theme.of(context).textTheme.titleLarge
                              ?.copyWith(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Using ${pred.modelUsed == 'ml' ? 'ML Model' : 'Rule-Based'} Prediction',
                    style: Theme.of(
                      context,
                    ).textTheme.bodySmall?.copyWith(color: Colors.white70),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            /// Machinery section
            if ((pred.machinery).isNotEmpty) ...[
              _buildSectionHeader(context, Icons.construction, 'Machinery'),
              const SizedBox(height: 8),
              ...pred.machinery.map((m) => _buildItemChip(context, m)),
              const SizedBox(height: 20),
            ],

            /// Vehicles section
            if ((pred.vehicles).isNotEmpty) ...[
              _buildSectionHeader(context, Icons.local_shipping, 'Vehicles'),
              const SizedBox(height: 8),
              ...pred.vehicles.map((v) => _buildItemChip(context, v)),
              const SizedBox(height: 20),
            ],

            /// Labour section
            _buildSectionHeader(context, Icons.people, 'Labour Required'),
            const SizedBox(height: 12),
            _buildLabourStats(
              context,
              colorScheme,
              pred.labourSkilled,
              pred.labourUnskilled,
            ),
            const SizedBox(height: 20),

            /// Fuel plan section
            if (pred.fuelPlan != null) ...[
              _buildSectionHeader(
                context,
                Icons.local_gas_station,
                'Fuel Plan',
              ),
              const SizedBox(height: 12),
              _buildFuelPlanSummary(context, colorScheme, pred.fuelPlan!),
              const SizedBox(height: 20),
            ],

            /// Action buttons
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.file_download),
                    label: const Text('Download Report'),
                    onPressed: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Report download coming soon'),
                        ),
                      );
                    },
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton.icon(
                  icon: const Icon(Icons.edit),
                  label: const Text('Edit'),
                  onPressed: () => setState(() => _prediction = null),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  /// Build section header
  Widget _buildSectionHeader(
    BuildContext context,
    IconData icon,
    String title,
  ) {
    return Row(
      children: [
        Icon(icon, color: Theme.of(context).colorScheme.primary),
        const SizedBox(width: 8),
        Text(
          title,
          style: Theme.of(
            context,
          ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
        ),
      ],
    );
  }

  /// Build item chip
  Widget _buildItemChip(BuildContext context, String item) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Chip(
        label: Text(item),
        avatar: Icon(
          Icons.check_circle_outline,
          color: Theme.of(context).colorScheme.primary,
        ),
      ),
    );
  }

  /// Build labour stats
  Widget _buildLabourStats(
    BuildContext context,
    ColorScheme colorScheme,
    int skilled,
    int unskilled,
  ) {
    return Row(
      children: [
        Expanded(
          child: _buildStatBox(
            context,
            colorScheme,
            'Skilled',
            skilled.toString(),
            Colors.blue,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildStatBox(
            context,
            colorScheme,
            'Unskilled',
            unskilled.toString(),
            Colors.orange,
          ),
        ),
      ],
    );
  }

  /// Build stat box
  Widget _buildStatBox(
    BuildContext context,
    ColorScheme colorScheme,
    String label,
    String value,
    Color color,
  ) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          children: [
            Text(
              value,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            const SizedBox(height: 4),
            Text(label, style: Theme.of(context).textTheme.labelSmall),
          ],
        ),
      ),
    );
  }

  /// Build fuel plan summary
  Widget _buildFuelPlanSummary(
    BuildContext context,
    ColorScheme colorScheme,
    FuelPlan fuelPlan,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        /// Total liters
        Card(
          color: colorScheme.primary.withOpacity(0.1),
          child: Padding(
            padding: const EdgeInsets.all(12.0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Total Fuel Required',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    Text(
                      '${fuelPlan.totalLiters.toStringAsFixed(0)} Liters',
                      style: Theme.of(context).textTheme.headlineSmall
                          ?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: colorScheme.primary,
                          ),
                    ),
                  ],
                ),
                Icon(
                  Icons.local_gas_station,
                  size: 40,
                  color: colorScheme.primary,
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),

        /// Fuel by type
        if (fuelPlan.summaryByFuelType.isNotEmpty) ...[
          Text(
            'Breakdown by Fuel Type',
            style: Theme.of(
              context,
            ).textTheme.labelMedium?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          ...fuelPlan.summaryByFuelType.entries
              .map(
                (e) => Padding(
                  padding: const EdgeInsets.only(bottom: 4.0),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(e.key),
                      Text(
                        '${e.value.toStringAsFixed(0)} L',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
              )
              .toList(),
        ],
      ],
    );
  }
}
