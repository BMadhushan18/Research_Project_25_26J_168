import 'package:flutter/material.dart';
import '../../utils/constants.dart';
import 'phase_result.dart';

class StructuralWallDurationScreen extends StatefulWidget {
  final int initialLabors;

  const StructuralWallDurationScreen({
    super.key,
    this.initialLabors = 5,
  });

  @override
  State<StructuralWallDurationScreen> createState() => _StructuralWallDurationScreenState();
}

class _StructuralWallDurationScreenState extends State<StructuralWallDurationScreen> {
  final _formKey = GlobalKey<FormState>();

  String _wallType = 'Brick';

  final TextEditingController _floorAreaCtrl = TextEditingController();
  final TextEditingController _wallAreaCtrl = TextEditingController();

  int _laborCount = 5;

  final List<String> _wallTypes = const ['Brick', 'Concrete'];

  @override
  void initState() {
    super.initState();
    _laborCount = widget.initialLabors < 1 ? 1 : widget.initialLabors;
  }

  @override
  void dispose() {
    _floorAreaCtrl.dispose();
    _wallAreaCtrl.dispose();
    super.dispose();
  }

  // ----------------------------- Estimation Logic ----------------------------
  // Baseline productivity (m²/day) for 5 labors:
  // - Brick is slower than Concrete block walls.
  int _estimateWallDays({
    required String wallType,
    required double floorAreaM2,
    required double wallAreaM2,
    required int laborCount,
  }) {
    // sanity fallback: if wall area not provided properly, estimate from floor area
    // (typical relation: wallArea ≈ floorArea * 1.7)
    final effectiveWallArea = wallAreaM2 > 0 ? wallAreaM2 : (floorAreaM2 * 1.7);

    // base m2/day for 5 labors
    double baseM2PerDay = wallType == 'Brick' ? 18.0 : 24.0;

    // labor scaling (diminishing returns)
    final lc = laborCount.clamp(1, 50);
    double laborEfficiency = lc / 5.0;
    laborEfficiency = (laborEfficiency <= 2.0)
        ? laborEfficiency
        : (2.0 + (laborEfficiency - 2.0) * 0.6);

    final effectiveM2PerDay = baseM2PerDay * laborEfficiency;

    // duration = area / productivity
    final rawDays = effectiveWallArea / (effectiveM2PerDay <= 0 ? 0.1 : effectiveM2PerDay);

    // overhead days (setting out, curing, lintels etc.)
    final overheadDays = wallType == 'Brick' ? 2.0 : 1.5;

    final days = (rawDays + overheadDays).round();
    return days < 1 ? 1 : days;
  }

  void _onCalculate() {
    if (!_formKey.currentState!.validate()) return;

    final floorArea = double.parse(_floorAreaCtrl.text.trim());
    final wallArea = double.parse(_wallAreaCtrl.text.trim());

    final days = _estimateWallDays(
      wallType: _wallType,
      floorAreaM2: floorArea,
      wallAreaM2: wallArea,
      laborCount: _laborCount,
    );

    Navigator.pop(
      context,
      PhaseResult(
        durationDays: days,
        laborCount: _laborCount,
      ),
    );
  }

  // ----------------------------- UI -----------------------------------------
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Structural & Wall'),
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

              _buildDropdown(
                label: 'Wall Type',
                value: _wallType,
                items: _wallTypes,
                icon: Icons.construction_rounded,
                onChanged: (v) => setState(() => _wallType = v!),
              ),
              const SizedBox(height: 14),

              _buildNumberField(
                controller: _floorAreaCtrl,
                label: 'Floor Area (m²)',
                icon: Icons.crop_square_rounded,
                hint: 'e.g. 120',
              ),
              const SizedBox(height: 14),

              _buildNumberField(
                controller: _wallAreaCtrl,
                label: 'Wall Area (m²)',
                icon: Icons.view_quilt_rounded,
                hint: 'e.g. 210',
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
            child: const Icon(Icons.home_work_rounded, color: AppColors.primary),
          ),
          const SizedBox(width: 12),
          const Expanded(
            child: Text(
              'Fill wall details and calculate estimated duration (days).',
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
