import 'package:flutter/material.dart';
import '../../utils/constants.dart';
import 'phase_result.dart';

/// ---------------------------------------------------------------------------
/// DoorsWindowsDurationScreen
/// - Fields:
///   1) Doors Count
///   2) Door Material (dropdown): Aluminium, Timber, Glass, uPVC
///   3) Window Count
///   4) Window Material (dropdown): Aluminium, Timber, Glass, uPVC
///   5) Labor Count (counter)
/// - On Calculate:
///   -> estimate duration days
///   -> return result to PhaseWiseDurationScreen via Navigator.pop(result)
/// ---------------------------------------------------------------------------

class DoorsWindowsDurationScreen extends StatefulWidget {
  final int initialLabors;

  const DoorsWindowsDurationScreen({
    super.key,
    this.initialLabors = 5,
  });

  @override
  State<DoorsWindowsDurationScreen> createState() => _DoorsWindowsDurationScreenState();
}

class _DoorsWindowsDurationScreenState extends State<DoorsWindowsDurationScreen> {
  final _formKey = GlobalKey<FormState>();

  final TextEditingController _doorCountCtrl = TextEditingController();
  final TextEditingController _windowCountCtrl = TextEditingController();

  String _doorMaterial = 'Timber';
  String _windowMaterial = 'Timber';
  int _laborCount = 5;

  final List<String> _materials = const ['Aluminium', 'Timber', 'Glass', 'uPVC'];

  @override
  void initState() {
    super.initState();
    _laborCount = widget.initialLabors < 1 ? 1 : widget.initialLabors;
  }

  @override
  void dispose() {
    _doorCountCtrl.dispose();
    _windowCountCtrl.dispose();
    super.dispose();
  }

  // ----------------------------- Estimation Logic ----------------------------
  // Approx. productivity (units/day) for 5 labors, based on your earlier notes:
  // Doors per day:
  // - Timber: 2
  // - Aluminium: 3.5 (avg of 3-4)
  // - uPVC: 4
  // - Glass: 2.5 (avg of 2-3)
  //
  // Windows are similar but slightly faster/slower depending on site;
  // we'll use a close baseline.
  int _estimateDoorsWindowsDays({
    required int doorCount,
    required String doorMaterial,
    required int windowCount,
    required String windowMaterial,
    required int laborCount,
  }) {
    final Map<String, double> doorsPerDay5Labors = {
      'Timber': 2.0,
      'Aluminium': 3.5,
      'uPVC': 4.0,
      'Glass': 2.5,
    };

    final Map<String, double> windowsPerDay5Labors = {
      // windows often similar; we keep close baselines
      'Timber': 3.0,
      'Aluminium': 4.0,
      'uPVC': 4.5,
      'Glass': 3.0,
    };

    final doorRate = doorsPerDay5Labors[doorMaterial] ?? 3.0;
    final windowRate = windowsPerDay5Labors[windowMaterial] ?? 3.5;

    // labor scaling (diminishing returns after ~10)
    final lc = laborCount.clamp(1, 50);
    double laborEfficiency = lc / 5.0;
    laborEfficiency = (laborEfficiency <= 2.0)
        ? laborEfficiency
        : (2.0 + (laborEfficiency - 2.0) * 0.6);

    final effectiveDoorRate = doorRate * laborEfficiency;
    final effectiveWindowRate = windowRate * laborEfficiency;

    final doorDays = doorCount / (effectiveDoorRate <= 0 ? 0.1 : effectiveDoorRate);
    final windowDays = windowCount / (effectiveWindowRate <= 0 ? 0.1 : effectiveWindowRate);

    // some tasks can overlap; but still not fully parallel.
    // We use combined time with partial overlap.
    final combined = (doorDays + windowDays) * 0.85;

    // overhead: measurements, sealing, finishing
    final overhead = (doorCount + windowCount) > 12 ? 2.0 : 1.0;

    final days = (combined + overhead).round();
    return days < 1 ? 1 : days;
  }

  void _onCalculate() {
    if (!_formKey.currentState!.validate()) return;

    final doorCount = int.parse(_doorCountCtrl.text.trim());
    final windowCount = int.parse(_windowCountCtrl.text.trim());

    final days = _estimateDoorsWindowsDays(
      doorCount: doorCount,
      doorMaterial: _doorMaterial,
      windowCount: windowCount,
      windowMaterial: _windowMaterial,
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
        title: const Text('Doors & Windows Fixture'),
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

              _buildIntField(
                controller: _doorCountCtrl,
                label: 'Doors Count',
                icon: Icons.door_front_door_rounded,
                hint: 'e.g. 6',
              ),
              const SizedBox(height: 14),

              _buildDropdown(
                label: 'Door Material',
                value: _doorMaterial,
                items: _materials,
                icon: Icons.category_rounded,
                onChanged: (v) => setState(() => _doorMaterial = v!),
              ),
              const SizedBox(height: 14),

              _buildIntField(
                controller: _windowCountCtrl,
                label: 'Window Count',
                icon: Icons.window_rounded,
                hint: 'e.g. 8',
              ),
              const SizedBox(height: 14),

              _buildDropdown(
                label: 'Window Material',
                value: _windowMaterial,
                items: _materials,
                icon: Icons.category_rounded,
                onChanged: (v) => setState(() => _windowMaterial = v!),
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
            child: const Icon(Icons.door_sliding_rounded, color: AppColors.primary),
          ),
          const SizedBox(width: 12),
          const Expanded(
            child: Text(
              'Fill doors & windows details and calculate estimated duration (days).',
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

  Widget _buildIntField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    String? hint,
  }) {
    return TextFormField(
      controller: controller,
      keyboardType: TextInputType.number,
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
        final n = int.tryParse(v.trim());
        if (n == null) return 'Enter a valid number';
        if (n < 0) return '$label cannot be negative';
        if (n == 0) return '$label must be at least 1';
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
