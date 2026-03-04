import 'package:flutter/material.dart';
import '../../utils/constants.dart';
import 'phase_result.dart';

/// ---------------------------------------------------------------------------
/// RoofDurationScreen
/// - Fields:
///   1) Roof Area (m²)
///   2) Roof Height (m)
///   3) Roof Type (dropdown): Gable, Flat, Lean-to, Hip
///   4) Roof Covering Type (dropdown): Concrete Tiles, Clay Tiles, RC Slab,
///                                    Asbestos Sheets, Metal Sheets
///   5) Labor Count (counter)
/// - On Calculate:
///   -> estimate duration days
///   -> return result to PhaseWiseDurationScreen via Navigator.pop(result)
/// ---------------------------------------------------------------------------

class RoofDurationScreen extends StatefulWidget {
  final int initialLabors;

  const RoofDurationScreen({
    super.key,
    this.initialLabors = 5,
  });

  @override
  State<RoofDurationScreen> createState() => _RoofDurationScreenState();
}

class _RoofDurationScreenState extends State<RoofDurationScreen> {
  final _formKey = GlobalKey<FormState>();

  final TextEditingController _roofAreaCtrl = TextEditingController();
  final TextEditingController _roofHeightCtrl = TextEditingController();

  String _roofType = 'Gable';
  String _coveringType = 'Concrete Tiles';
  int _laborCount = 5;

  final List<String> _roofTypes = const ['Gable', 'Flat', 'Lean-to', 'Hip'];
  final List<String> _coveringTypes = const [
    'Concrete Tiles',
    'Clay Tiles',
    'RC Slab',
    'Asbestos Sheets',
    'Metal Sheets',
  ];

  @override
  void initState() {
    super.initState();
    _laborCount = widget.initialLabors < 1 ? 1 : widget.initialLabors;
  }

  @override
  void dispose() {
    _roofAreaCtrl.dispose();
    _roofHeightCtrl.dispose();
    super.dispose();
  }

  // ----------------------------- Estimation Logic ----------------------------
  // We estimate "effective productivity" in m²/day for 5 labors,
  // then adjust by roof type + covering type + height + labor count.
  int _estimateRoofDays({
    required double roofAreaM2,
    required double roofHeightM,
    required String roofType,
    required String coveringType,
    required int laborCount,
  }) {
    // baseline m²/day for 5 labors, medium complexity
    double baseM2PerDay = 14.0;

    // roof type complexity factor (higher => slower)
    final Map<String, double> roofTypeFactor = {
      'Lean-to': 0.90, // simplest
      'Flat': 1.00,
      'Gable': 1.10,
      'Hip': 1.25,     // more cuts/angles
    };

    // covering type speed factor (higher => slower)
    final Map<String, double> coveringFactor = {
      'Metal Sheets': 0.85,      // fastest
      'Asbestos Sheets': 0.90,
      'Concrete Tiles': 1.10,
      'RC Slab': 1.20,
      'Clay Tiles': 1.25,        // slowest
    };

    final rt = roofTypeFactor[roofType] ?? 1.0;
    final cv = coveringFactor[coveringType] ?? 1.0;

    // height factor: higher roof => more scaffold / lifting time
    // typical 1.8–3.0m; above that gets slower
    double heightFactor = 1.0;
    if (roofHeightM > 3.0) heightFactor = 1.0 + ((roofHeightM - 3.0) * 0.08);
    if (roofHeightM < 1.5) heightFactor = 0.95;

    // labor scaling (diminishing returns after ~10)
    final lc = laborCount.clamp(1, 50);
    double laborEfficiency = lc / 5.0;
    laborEfficiency = (laborEfficiency <= 2.0)
        ? laborEfficiency
        : (2.0 + (laborEfficiency - 2.0) * 0.6);

    final effectiveM2PerDay =
        (baseM2PerDay / (rt * cv * heightFactor)) * laborEfficiency;

    final rawDays = roofAreaM2 / (effectiveM2PerDay <= 0 ? 0.1 : effectiveM2PerDay);

    // overhead: setup, material unloading, finishing edges
    final overhead = (coveringType == 'RC Slab') ? 3.0 : 2.0;

    final days = (rawDays + overhead).round();
    return days < 1 ? 1 : days;
  }

  void _onCalculate() {
    if (!_formKey.currentState!.validate()) return;

    final area = double.parse(_roofAreaCtrl.text.trim());
    final height = double.parse(_roofHeightCtrl.text.trim());

    final days = _estimateRoofDays(
      roofAreaM2: area,
      roofHeightM: height,
      roofType: _roofType,
      coveringType: _coveringType,
      laborCount: _laborCount,
    );

    Navigator.pop(
      context,
      PhaseResult(durationDays: days, laborCount: _laborCount),
    );
  }

  // ----------------------------- UI -----------------------------------------
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Roofing'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              _buildHeaderCard(),
              const SizedBox(height: 18),

              _buildNumberField(
                controller: _roofAreaCtrl,
                label: 'Roof Area (m²)',
                icon: Icons.crop_square_rounded,
                hint: 'e.g. 160',
              ),
              const SizedBox(height: 14),

              _buildNumberField(
                controller: _roofHeightCtrl,
                label: 'Roof Height (m)',
                icon: Icons.height_rounded,
                hint: 'e.g. 2.5',
              ),
              const SizedBox(height: 14),

              _buildDropdown(
                label: 'Roof Type',
                value: _roofType,
                items: _roofTypes,
                icon: Icons.home_work_rounded,
                onChanged: (v) => setState(() => _roofType = v!),
              ),
              const SizedBox(height: 14),

              _buildDropdown(
                label: 'Roof Covering Type',
                value: _coveringType,
                items: _coveringTypes,
                icon: Icons.roofing_rounded,
                onChanged: (v) => setState(() => _coveringType = v!),
              ),
              const SizedBox(height: 14),

              _buildCounterField(
                label: 'Labor Count',
                value: _laborCount,
                icon: Icons.groups_rounded,
                onChanged: (v) => setState(() => _laborCount = v),
              ),

              const SizedBox(height: 26),

              SizedBox(
                width: double.infinity,
                height: 54,
                child: ElevatedButton.icon(
                  onPressed: _onCalculate,
                  icon: const Icon(Icons.calculate_rounded),
                  label: const Text(
                    'Calculate',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primaryDark,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    elevation: 4,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeaderCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.borderLight),
      ),
      child: Row(
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: AppColors.primary.withOpacity(0.12),
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Icon(Icons.roofing_rounded, color: AppColors.primary),
          ),
          const SizedBox(width: 12),
          const Expanded(
            child: Text(
              'Fill roofing details and calculate estimated duration (days).',
              style: TextStyle(
                color: AppColors.textSecondary,
                height: 1.3,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDropdown({
    required String label,
    required String value,
    required List<String> items,
    required IconData icon,
    required ValueChanged<String?> onChanged,
  }) {
    return DropdownButtonFormField<String>(
      value: value,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: AppColors.primary),
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
      ),
      items: items.map((i) => DropdownMenuItem(value: i, child: Text(i))).toList(),
      onChanged: onChanged,
    );
  }

  Widget _buildNumberField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    String? hint,
  }) {
    return TextFormField(
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        prefixIcon: Icon(icon, color: AppColors.primary),
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
      ),
      validator: (v) {
        if (v == null || v.trim().isEmpty) return 'Please enter $label';
        final n = double.tryParse(v.trim());
        if (n == null) return 'Enter a valid number';
        if (n <= 0) return '$label must be greater than 0';
        return null;
      },
    );
  }

  Widget _buildCounterField({
    required String label,
    required int value,
    required IconData icon,
    required ValueChanged<int> onChanged,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.borderLight),
      ),
      child: Row(
        children: [
          Icon(icon, color: AppColors.primary),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              label,
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          IconButton(
            onPressed: () => value > 1 ? onChanged(value - 1) : null,
            icon: const Icon(Icons.remove_circle_outline, color: AppColors.error),
          ),
          Text(
            '$value',
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
          ),
          IconButton(
            onPressed: () => onChanged(value + 1),
            icon: const Icon(Icons.add_circle_outline, color: AppColors.success),
          ),
        ],
      ),
    );
  }
}


