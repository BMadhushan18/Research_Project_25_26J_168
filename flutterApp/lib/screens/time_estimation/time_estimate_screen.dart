import 'package:flutter/material.dart';
import '../../utils/constants.dart';
import 'estimation_result_screen.dart';

class TimeEstimateScreen extends StatefulWidget {
  const TimeEstimateScreen({super.key});

  @override
  State<TimeEstimateScreen> createState() => _TimeEstimateScreenState();
}

class _TimeEstimateScreenState extends State<TimeEstimateScreen> {
  final _formKey = GlobalKey<FormState>();

  // Controllers and State Variables
  final TextEditingController _areaController = TextEditingController();
  int _floorCount = 1;
  int _laborCount = 5;

  String _selectedFoundation = 'Concrete';
  String _selectedWall = 'Brick';
  String _selectedRoofing = 'Concrete Tiles';
  String _selectedFlooring = 'Tiles';

  // Dropdown Options
  final List<String> _foundations = ['Rubble', 'Concrete', 'Strip', 'Pile', 'Raft'];
  final List<String> _walls = ['Concrete Block', 'Brick'];
  final List<String> _roofingTypes = ['Asbestos Sheet', 'Concrete Tiles', 'Clay Tiles', 'Metal Sheets'];
  final List<String> _flooringTypes = ['Cement Rendering', 'Tiles', 'Titanium', 'Hardwood'];

  @override
  void dispose() {
    _areaController.dispose();
    super.dispose();
  }

  /// Convert total days -> "X months Y weeks Z days"
  /// Practical approximation: 1 month = 30 days, 1 week = 7 days
  String _formatDurationFromDays(int totalDays) {
    final months = totalDays ~/ 30;
    final afterMonths = totalDays % 30;
    final weeks = afterMonths ~/ 7;
    final days = afterMonths % 7;

    final parts = <String>[];
    if (months > 0) parts.add('$months month${months == 1 ? '' : 's'}');
    if (weeks > 0) parts.add('$weeks week${weeks == 1 ? '' : 's'}');
    if (days > 0 || parts.isEmpty) parts.add('$days day${days == 1 ? '' : 's'}');

    return parts.join(' ');
  }

  /// TEMP local estimate -> returns DAYS (int)
  /// Later you will replace this with backend model prediction (duration_days).
  int _estimateDaysLocally({
    required double areaSqft,
    required int floors,
    required int laborCount,
  }) {
    // Placeholder logic (simple + stable):
    // - bigger area => more days
    // - more floors => more days
    // - more labor => fewer days (but clamp so it doesn't go unreal)
    final baseDays = areaSqft / 20;              // e.g., 2000 sqft ~ 100 days
    final floorDays = (floors - 1) * 10;         // extra per additional floor
    final laborFactor = (5 / laborCount).clamp(0.25, 2.5); // more labor => smaller factor

    final estimated = ((baseDays + floorDays) * laborFactor).round();
    return estimated < 1 ? 1 : estimated;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Time Estimation Form'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            _buildHeader(),
            Padding(
              padding: const EdgeInsets.all(20.0),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildSectionTitle('General Specifications'),
                    _buildTextField(
                      _areaController,
                      'Building Area (Sqft)',
                      Icons.crop_square,
                      TextInputType.number,
                    ),
                    const SizedBox(height: 16),

                    _buildCounterField(
                      'Number of Floors',
                      _floorCount,
                      (val) => setState(() => _floorCount = val),
                      Icons.layers,
                    ),

                    const SizedBox(height: 24),
                    _buildSectionTitle('Material Selection'),

                    _buildDropdown(
                      'Foundation Type',
                      _selectedFoundation,
                      _foundations,
                      (val) => setState(() => _selectedFoundation = val!),
                      Icons.account_balance,
                    ),

                    _buildDropdown(
                      'Wall Material',
                      _selectedWall,
                      _walls,
                      (val) => setState(() => _selectedWall = val!),
                      Icons.construction,
                    ),

                    _buildDropdown(
                      'Roofing Type',
                      _selectedRoofing,
                      _roofingTypes,
                      (val) => setState(() => _selectedRoofing = val!),
                      Icons.home,
                    ),

                    _buildDropdown(
                      'Flooring Type',
                      _selectedFlooring,
                      _flooringTypes,
                      (val) => setState(() => _selectedFlooring = val!),
                      Icons.view_module,
                    ),

                    const SizedBox(height: 24),
                    _buildSectionTitle('Labor Resource'),

                    _buildCounterField(
                      'Average Labor Count',
                      _laborCount,
                      (val) => setState(() => _laborCount = val),
                      Icons.groups,
                    ),

                    const SizedBox(height: 40),
                    _buildSubmitButton(),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 30, horizontal: 20),
      decoration: BoxDecoration(
        color: AppColors.primary,
        borderRadius: const BorderRadius.only(
          bottomLeft: Radius.circular(30),
          bottomRight: Radius.circular(30),
        ),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Calculate Project Duration',
            style: TextStyle(
              color: Colors.white,
              fontSize: 22,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 8),
          Text(
            'Enter the building details below to estimate the time required for completion.',
            style: TextStyle(color: Colors.white70, fontSize: 14),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16, top: 8),
      child: Text(
        title,
        style: TextStyle(
          color: AppColors.primary,
          fontSize: 16,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _buildTextField(
    TextEditingController controller,
    String label,
    IconData icon,
    TextInputType type,
  ) {
    return TextFormField(
      controller: controller,
      keyboardType: type,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: AppColors.primary),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        filled: true,
        fillColor: Colors.white,
      ),
      validator: (v) {
        if (v == null || v.trim().isEmpty) return 'Please enter $label';
        final n = double.tryParse(v.trim());
        if (n == null) return 'Please enter a valid number';
        if (n <= 0) return '$label must be greater than 0';
        return null;
      },
    );
  }

  Widget _buildCounterField(
    String label,
    int value,
    Function(int) onChanged,
    IconData icon,
  ) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey.shade400),
        borderRadius: BorderRadius.circular(12),
        color: Colors.white,
      ),
      child: Row(
        children: [
          Icon(icon, color: AppColors.primary),
          const SizedBox(width: 12),
          Expanded(child: Text(label, style: const TextStyle(fontSize: 16))),
          IconButton(
            onPressed: () => value > 1 ? onChanged(value - 1) : null,
            icon: const Icon(Icons.remove_circle_outline, color: Colors.red),
          ),
          Text(
            '$value',
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          IconButton(
            onPressed: () => onChanged(value + 1),
            icon: const Icon(Icons.add_circle_outline, color: Colors.green),
          ),
        ],
      ),
    );
  }

  Widget _buildDropdown(
    String label,
    String value,
    List<String> items,
    Function(String?) onChanged,
    IconData icon,
  ) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: DropdownButtonFormField<String>(
        value: value,
        decoration: InputDecoration(
          labelText: label,
          prefixIcon: Icon(icon, color: AppColors.primary),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
          filled: true,
          fillColor: Colors.white,
        ),
        items: items.map((i) => DropdownMenuItem(value: i, child: Text(i))).toList(),
        onChanged: onChanged,
      ),
    );
  }

  Widget _buildSubmitButton() {
    return SizedBox(
      width: double.infinity,
      height: 55,
      child: ElevatedButton(
        onPressed: () {
          if (!_formKey.currentState!.validate()) return;

          final area = double.parse(_areaController.text.trim());

          // ✅ For now: local estimate in DAYS
          // Later: call backend model -> duration_days
          final estimatedDays = _estimateDaysLocally(
            areaSqft: area,
            floors: _floorCount,
            laborCount: _laborCount,
          );

          final pretty = _formatDurationFromDays(estimatedDays);

          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => EstimationResultScreen(
                durationDays: estimatedDays,
                durationText: pretty,
              ),
            ),
          );
        },
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primary,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
        child: const Text(
          'Calculate Duration',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
      ),
    );
  }
}