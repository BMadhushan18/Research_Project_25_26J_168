import 'package:flutter/material.dart';
import '../../utils/constants.dart';
import 'phase_result.dart';

class FoundationDurationScreen extends StatefulWidget {
  final int initialLabors;

  const FoundationDurationScreen({
    super.key,
    this.initialLabors = 5,
  });

  @override
  State<FoundationDurationScreen> createState() => _FoundationDurationScreenState();
}

class _FoundationDurationScreenState extends State<FoundationDurationScreen> {
  final _formKey = GlobalKey<FormState>();

  // dropdowns
  String _foundationType = 'Concrete';
  String _soilType = 'Normal';

  // inputs
  final TextEditingController _volumeCtrl = TextEditingController();
  int _laborCount = 5;

  final List<String> _foundationTypes = const ['Rubble', 'Concrete', 'Strip', 'Pile', 'Raft'];
  final List<String> _soilTypes = const ['Soft', 'Normal', 'Hard'];

  @override
  void initState() {
    super.initState();
    _laborCount = widget.initialLabors < 1 ? 1 : widget.initialLabors;
  }

  @override
  void dispose() {
    _volumeCtrl.dispose();
    super.dispose();
  }

  // ----------------------------- Estimation Logic ----------------------------
  // Practical baseline productivity (m3/day) for 5 labors, Normal soil.
  // Then adjust for foundation type + soil type + labor count.
  int _estimateFoundationDays({
    required String foundationType,
    required String soilType,
    required double volumeM3,
    required int laborCount,
  }) {
    // base m3/day with 5 labors (Normal soil, Concrete base)
    double baseM3PerDay = 2.2;

    // foundation complexity factor (higher => slower)
    final Map<String, double> foundationFactor = {
      'Rubble': 1.10,
      'Concrete': 1.00,
      'Strip': 1.05,
      'Pile': 1.45,
      'Raft': 1.25,
    };

    // soil difficulty factor
    final Map<String, double> soilFactor = {
      'Soft': 1.20,    // more shoring / collapse risk
      'Normal': 1.00,
      'Hard': 1.30,    // harder excavation
    };

    final f = foundationFactor[foundationType] ?? 1.0;
    final s = soilFactor[soilType] ?? 1.0;

    // labor scaling: diminishing returns after ~10
    final lc = laborCount.clamp(1, 50);
    double laborEfficiency = lc / 5.0;
    // diminishing returns
    laborEfficiency = (laborEfficiency <= 2.0)
        ? laborEfficiency
        : (2.0 + (laborEfficiency - 2.0) * 0.6);

    final effectiveM3PerDay = (baseM3PerDay / (f * s)) * laborEfficiency;

    // duration = volume / productivity
    final rawDays = volumeM3 / (effectiveM3PerDay <= 0 ? 0.1 : effectiveM3PerDay);

    // add small fixed overhead (setting out, curing prep etc.)
    final overheadDays = foundationType == 'Pile' ? 2.0 : 1.0;

    final days = (rawDays + overheadDays).round();
    return days < 1 ? 1 : days;
  }

  void _onCalculate() {
    if (!_formKey.currentState!.validate()) return;

    final volume = double.parse(_volumeCtrl.text.trim());
    final days = _estimateFoundationDays(
      foundationType: _foundationType,
      soilType: _soilType,
      volumeM3: volume,
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
        title: const Text('Foundation'),
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
                label: 'Foundation Type',
                value: _foundationType,
                items: _foundationTypes,
                icon: Icons.account_balance_rounded,
                onChanged: (v) => setState(() => _foundationType = v!),
              ),
              const SizedBox(height: 14),

              _buildDropdown(
                label: 'Soil Type',
                value: _soilType,
                items: _soilTypes,
                icon: Icons.terrain_rounded,
                onChanged: (v) => setState(() => _soilType = v!),
              ),
              const SizedBox(height: 14),

              _buildNumberField(
                controller: _volumeCtrl,
                label: 'Volume (m³)',
                icon: Icons.square_foot_rounded,
                hint: 'e.g. 18.5',
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
            child: const Icon(Icons.foundation_rounded, color: AppColors.primary),
          ),
          const SizedBox(width: 12),
          const Expanded(
            child: Text(
              'Fill foundation details and calculate estimated duration (days).',
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
