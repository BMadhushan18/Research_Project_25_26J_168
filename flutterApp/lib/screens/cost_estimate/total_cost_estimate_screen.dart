import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/mongo_project_provider.dart';
import '../../services/mongo_api_service.dart';
import '../../utils/constants.dart';

class TotalCostEstimateScreen extends StatefulWidget {
  final String? uid;
  final String? pid;
  final String? projectName;
  final String? location;
  final String? userName;
  final String? userEmail;

  const TotalCostEstimateScreen({
    super.key,
    this.uid,
    this.pid,
    this.projectName,
    this.location,
    this.userName,
    this.userEmail,
  });

  @override
  State<TotalCostEstimateScreen> createState() =>
      _TotalCostEstimateScreenState();
}

class _TotalCostEstimateScreenState extends State<TotalCostEstimateScreen> {
  final Set<String> _expandedTitles = <String>{};
  final MongoApiService _api = MongoApiService();

  double? _materialCost;
  bool _materialLoading = false;
  String? _materialError;

  double? _laborCost;
  double? _machineryCost;
  double? _vehicleCost;
  bool _boqPredictionLoading = false;
  String? _boqPredictionError;

  @override
  void initState() {
    super.initState();
    _prefetchCostsForTotal();
  }

  Future<void> _prefetchCostsForTotal() async {
    // Load both sources up-front so Total Cost is ready without tile clicks.
    await Future.wait([
      _fetchMaterialCost(),
      _fetchBoqPredictionCosts(),
    ]);
  }

  void _toggleExpanded(String title) {
    setState(() {
      if (_expandedTitles.contains(title)) {
        _expandedTitles.remove(title);
      } else {
        _expandedTitles.add(title);
      }
    });
  }

  String? _resolveProjectId() {
    if ((widget.pid ?? '').trim().isNotEmpty) return widget.pid!.trim();
    final current = context.read<MongoProjectProvider>().currentProject;
    final fromProvider = current?.projectId ?? '';
    if (fromProvider.trim().isNotEmpty) return fromProvider.trim();
    return null;
  }

  Future<void> _fetchMaterialCost() async {
    final pid = _resolveProjectId();
    if (pid == null) {
      setState(() {
        _materialError = 'Project ID not found.';
      });
      return;
    }

    setState(() {
      _materialLoading = true;
      _materialError = null;
    });

    try {
      final total = await _api.getBoqReportGrandTotal(pid);
      if (!mounted) return;
      setState(() {
        _materialCost = total;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _materialError = e.toString().replaceFirst('Exception: ', '');
      });
    } finally {
      if (!mounted) return;
      setState(() {
        _materialLoading = false;
      });
    }
  }

  Future<void> _onMaterialCostTap() async {
    final wasExpanded = _expandedTitles.contains('Material Cost');
    _toggleExpanded('Material Cost');

    // Fetch only when opening details for the first time.
    if (!wasExpanded && _materialCost == null && !_materialLoading) {
      await _fetchMaterialCost();
    }
  }

  Future<void> _fetchBoqPredictionCosts() async {
    final pid = _resolveProjectId();
    if (pid == null) {
      setState(() {
        _boqPredictionError = 'Project ID not found.';
      });
      return;
    }

    setState(() {
      _boqPredictionLoading = true;
      _boqPredictionError = null;
    });

    try {
      final costs = await _api.getBoqPredictionCosts(pid);
      if (!mounted) return;
      setState(() {
        _laborCost = costs['labor_cost_lkr'] ?? 0.0;
        _machineryCost = costs['machinery_cost_lkr'] ?? 0.0;
        _vehicleCost = costs['vehicle_cost_lkr'] ?? 0.0;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _boqPredictionError = e.toString().replaceFirst('Exception: ', '');
      });
    } finally {
      if (!mounted) return;
      setState(() {
        _boqPredictionLoading = false;
      });
    }
  }

  Future<void> _onCostTileTap(String title) async {
    final wasExpanded = _expandedTitles.contains(title);
    _toggleExpanded(title);

    final hasData =
        _laborCost != null && _machineryCost != null && _vehicleCost != null;

    if (!wasExpanded && !hasData && !_boqPredictionLoading) {
      await _fetchBoqPredictionCosts();
    }
  }

  String _formatCurrency(num value) {
    final fixed = value.toStringAsFixed(2);
    final parts = fixed.split('.');
    final integer = parts[0].replaceAllMapped(
      RegExp(r'\B(?=(\d{3})+(?!\d))'),
      (_) => ',',
    );
    return 'Rs. $integer.${parts[1]}';
  }

  String get _materialDetailsText {
    if (_materialLoading) {
      return 'Loading material cost...';
    }
    if (_materialError != null && _materialError!.isNotEmpty) {
      return '';
    }
    if (_materialCost != null) {
      return 'Material Cost (LKR): Rs. ${_formatCurrency(_materialCost!)}';
    }
    return '';
  }

  String _buildCostDetailsText({
    required String label,
    required double? value,
  }) {
    if (_boqPredictionLoading) return 'Loading $label...';
    if (_boqPredictionError != null && _boqPredictionError!.isNotEmpty) {
      return '';
    }
    if (value != null) return '$label: ${_formatCurrency(value)}';
    return '';
  }

  double get _totalCostValue =>
      (_materialCost ?? 0.0) +
      (_laborCost ?? 0.0) +
      (_machineryCost ?? 0.0) +
      (_vehicleCost ?? 0.0);

  @override
  Widget build(BuildContext context) {
    final projectProvider = context.watch<MongoProjectProvider>();
    final currentProject = projectProvider.currentProject;

    final resolvedProjectName =
        widget.projectName ?? currentProject?.projectName ?? 'Unnamed Project';
    final resolvedLocation =
        widget.location ?? currentProject?.location ?? 'Unknown Location';

    return Scaffold(
      backgroundColor: const Color(0xFFF3F4F6),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(14, 14, 14, 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildTopSummaryCard(
              projectName: resolvedProjectName,
              location: resolvedLocation,
            ),
            const SizedBox(height: 14),
            _buildTotalCostCard(),
            const SizedBox(height: 16),

            Row(
              children: [
                Text(
                  'Cost Breakdown',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Divider(
                    color: Colors.grey.shade300,
                    thickness: 1,
                  ),
                ),
              ],
            ),

            const SizedBox(height: 10),

            _buildBreakdownTile(
              context,
              icon: Icons.inventory_2,
              title: 'Material Cost',
              isExpanded: _expandedTitles.contains('Material Cost'),
              onTap: _onMaterialCostTap,
              detailsText: _materialDetailsText,
            ),
            const SizedBox(height: 10),

            _buildBreakdownTile(
              context,
              icon: Icons.engineering,
              title: 'Labor Cost',
              isExpanded: _expandedTitles.contains('Labor Cost'),
              onTap: () => _onCostTileTap('Labor Cost'),
              detailsText: _buildCostDetailsText(
                label: 'Labor Cost (LKR)',
                value: _laborCost,
              ),
            ),
            const SizedBox(height: 10),

            _buildBreakdownTile(
              context,
              icon: Icons.precision_manufacturing,
              title: 'Machinery Cost',
              isExpanded: _expandedTitles.contains('Machinery Cost'),
              onTap: () => _onCostTileTap('Machinery Cost'),
              detailsText: _buildCostDetailsText(
                label: 'Machinery Cost (LKR)',
                value: _machineryCost,
              ),
            ),
            const SizedBox(height: 10),

            _buildBreakdownTile(
              context,
              icon: Icons.local_shipping,
              title: 'Vehicle Cost',
              isExpanded: _expandedTitles.contains('Vehicle Cost'),
              onTap: () => _onCostTileTap('Vehicle Cost'),
              detailsText: _buildCostDetailsText(
                label: 'Vehicle Cost (LKR)',
                value: _vehicleCost,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTopSummaryCard({
    required String projectName,
    required String location,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.borderLight),
        boxShadow: const [
          BoxShadow(
            color: AppColors.cardShadow,
            blurRadius: 10,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            projectName,
            style: const TextStyle(
              color: AppColors.textPrimary,
              fontSize: 20,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              const Icon(
                Icons.location_on_outlined,
                size: 16,
                color: AppColors.textSecondary,
              ),
              const SizedBox(width: 4),
              Expanded(
                child: Text(
                  location,
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildTotalCostCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.primary, AppColors.primaryLight],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withOpacity(0.25),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          const Text(
            'Total Cost',
            style: TextStyle(
              color: Colors.white,
              fontSize: 22,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 8),
          Container(
            width: double.infinity,
            height: 1,
            color: Colors.white.withOpacity(0.35),
          ),
          const SizedBox(height: 12),
          Text(
            _formatCurrency(_totalCostValue),
            style: const TextStyle(
              color: Colors.white,
              fontSize: 28,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBreakdownTile(
    BuildContext context, {
    required IconData icon,
    required String title,
    required bool isExpanded,
    required VoidCallback onTap,
    String? detailsText,
  }) {
    final safeDetailsText = (detailsText ?? '').trim();

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.grey.shade200),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          ListTile(
            contentPadding:
                const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
            leading: Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.10),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(
                icon,
                color: AppColors.primary,
                size: 24,
              ),
            ),
            title: Text(
              title,
              style: TextStyle(
                color: AppColors.textPrimary,
                fontWeight: FontWeight.w600,
                fontSize: 16,
              ),
            ),
              trailing: InkWell(
                onTap: onTap,
                borderRadius: BorderRadius.circular(20),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 180),
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: isExpanded
                        ? AppColors.primary
                        : AppColors.primary.withOpacity(0.10),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    isExpanded
                        ? Icons.keyboard_arrow_up_rounded
                        : Icons.keyboard_arrow_right_rounded,
                    color: isExpanded ? Colors.white : AppColors.primary,
                    size: 20,
                  ),
                ),
              ),
          ),
          AnimatedCrossFade(
            firstChild: const SizedBox.shrink(),
            secondChild: safeDetailsText.isEmpty
                ? const SizedBox.shrink()
                : Padding(
                    padding: const EdgeInsets.fromLTRB(14, 0, 14, 12),
                    child: Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: AppColors.primary.withOpacity(0.22)),
                        boxShadow: [
                          BoxShadow(
                            color: AppColors.primary.withOpacity(0.06),
                            blurRadius: 8,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                      child: _buildDetailsContent(safeDetailsText),
                    ),
                  ),
            crossFadeState: isExpanded
                ? CrossFadeState.showSecond
                : CrossFadeState.showFirst,
            duration: const Duration(milliseconds: 220),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailsContent(String text) {
    final valueText = text.trim();
    final parts = valueText.split(':');

    if (parts.length >= 2) {
      final label = parts.first.trim();
      final amount = parts.sublist(1).join(':').trim();

      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: TextStyle(
              color: AppColors.textSecondary,
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            amount,
            style: TextStyle(
              color: AppColors.textPrimary,
              fontSize: 20,
              fontWeight: FontWeight.w800,
              height: 1.15,
            ),
          ),
        ],
      );
    }

    return Text(
      valueText,
      style: TextStyle(
        color: AppColors.textPrimary,
        fontSize: 15,
        fontWeight: FontWeight.w600,
      ),
    );
  }

}