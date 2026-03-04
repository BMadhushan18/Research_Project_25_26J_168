import 'package:flutter/material.dart';
import '../../utils/constants.dart';
import 'foundation_duration_screen.dart';
import 'structural_wall_duration_screen.dart';
import 'roof_duration_screen.dart';
import 'doors_windows_duration_screen.dart';
import 'phase_result.dart';

class PhaseWiseDurationScreen extends StatefulWidget {
  const PhaseWiseDurationScreen({super.key});

  @override
  State<PhaseWiseDurationScreen> createState() => _PhaseWiseDurationScreenState();
}

class _PhaseWiseDurationScreenState extends State<PhaseWiseDurationScreen> {
  final List<_PhaseItem> _phases = [
    _PhaseItem(name: 'Foundation'),
    _PhaseItem(name: 'Structural and Wall'),
    _PhaseItem(name: 'Roofing'),
    _PhaseItem(name: 'Doors and Window Fixture'),
    _PhaseItem(name: 'Plumbing'),
    _PhaseItem(name: 'Electrical'),
    _PhaseItem(name: 'Plastering'),
    _PhaseItem(name: 'Flooring'),
    _PhaseItem(name: 'Painting and Finishing'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Phase Wise Duration'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: Column(
        children: [
          _buildHeader(),
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
              itemCount: _phases.length,
              separatorBuilder: (_, __) => const SizedBox(height: 14),
              itemBuilder: (context, index) {
                final p = _phases[index];
                return _buildPhaseCard(
                  phase: p,
                  index: index,
                  onTapCalculateOrEdit: () => _openPhaseForm(index),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(20, 22, 20, 22),
      decoration: const BoxDecoration(
        color: AppColors.primary,
        borderRadius: BorderRadius.only(
          bottomLeft: Radius.circular(26),
          bottomRight: Radius.circular(26),
        ),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Phase Wise Duration',
            style: TextStyle(
              color: Colors.white,
              fontSize: 22,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 6),
          Text(
            'Calculate duration for main construction phase.',
            style: TextStyle(
              color: Colors.white70,
              fontSize: 14,
              height: 1.3,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPhaseCard({
    required _PhaseItem phase,
    required int index,
    required VoidCallback onTapCalculateOrEdit,
  }) {
    final isCalculated = phase.isCalculated;

    return Container(
      decoration: BoxDecoration(
        color: AppColors.cardBackground,
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
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  '${index + 1}. ${phase.name}',
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              _StatusChip(isCalculated: isCalculated),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: _InfoPill(
                  icon: Icons.schedule_rounded,
                  label: 'Duration',
                  value: '${phase.durationDays} days',
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _InfoPill(
                  icon: Icons.groups_rounded,
                  label: 'Labors',
                  value: '${phase.laborCount}',
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton.icon(
              onPressed: onTapCalculateOrEdit,
              icon: Icon(isCalculated ? Icons.edit_rounded : Icons.calculate_rounded),
              label: Text(
                isCalculated ? 'Edit' : 'Calculate',
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: isCalculated ? AppColors.secondary : AppColors.primaryDark,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                elevation: 4,
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Wired screens:
  /// 0 -> FoundationDurationScreen
  /// 1 -> StructuralWallDurationScreen
  /// 2 -> RoofDurationScreen
  /// 3 -> DoorsWindowsDurationScreen ✅ NEW
  /// Others -> Coming soon
  Future<void> _openPhaseForm(int index) async {
    final phase = _phases[index];
    final initialLabors = phase.laborCount == 0 ? 5 : phase.laborCount;

    // 0 -> Foundation
    if (index == 0) {
      final result = await Navigator.push<PhaseResult>(
        context,
        MaterialPageRoute(
          builder: (_) => FoundationDurationScreen(initialLabors: initialLabors),
        ),
      );
      if (result == null) return;

      setState(() {
        _phases[index] = phase.copyWith(
          durationDays: result.durationDays,
          laborCount: result.laborCount,
          isCalculated: true,
        );
      });
      return;
    }

    // 1 -> Structural & Wall
    if (index == 1) {
      final result = await Navigator.push<PhaseResult>(
        context,
        MaterialPageRoute(
          builder: (_) => StructuralWallDurationScreen(initialLabors: initialLabors),
        ),
      );
      if (result == null) return;

      setState(() {
        _phases[index] = phase.copyWith(
          durationDays: result.durationDays,
          laborCount: result.laborCount,
          isCalculated: true,
        );
      });
      return;
    }

    // 2 -> Roofing
    if (index == 2) {
      final result = await Navigator.push<PhaseResult>(
        context,
        MaterialPageRoute(
          builder: (_) => RoofDurationScreen(initialLabors: initialLabors),
        ),
      );
      if (result == null) return;

      setState(() {
        _phases[index] = phase.copyWith(
          durationDays: result.durationDays,
          laborCount: result.laborCount,
          isCalculated: true,
        );
      });
      return;
    }

    // ✅ 3 -> Doors & Windows Fixture
    if (index == 3) {
      final result = await Navigator.push<PhaseResult>(
        context,
        MaterialPageRoute(
          builder: (_) => DoorsWindowsDurationScreen(initialLabors: initialLabors),
        ),
      );
      if (result == null) return;

      setState(() {
        _phases[index] = phase.copyWith(
          durationDays: result.durationDays,
          laborCount: result.laborCount,
          isCalculated: true,
        );
      });
      return;
    }

    // Others: not implemented yet
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text('This phase form is not implemented yet'),
        backgroundColor: AppColors.warning,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
    );
  }
}

/// ─────────────────────────────────────────────────────────────────────────────
/// Model
/// ─────────────────────────────────────────────────────────────────────────────

class _PhaseItem {
  final String name;
  final int durationDays;
  final int laborCount;
  final bool isCalculated;

  const _PhaseItem({
    required this.name,
    this.durationDays = 0,
    this.laborCount = 0,
    this.isCalculated = false,
  });

  _PhaseItem copyWith({
    String? name,
    int? durationDays,
    int? laborCount,
    bool? isCalculated,
  }) {
    return _PhaseItem(
      name: name ?? this.name,
      durationDays: durationDays ?? this.durationDays,
      laborCount: laborCount ?? this.laborCount,
      isCalculated: isCalculated ?? this.isCalculated,
    );
  }
}

/// ─────────────────────────────────────────────────────────────────────────────
/// UI components
/// ─────────────────────────────────────────────────────────────────────────────

class _StatusChip extends StatelessWidget {
  final bool isCalculated;

  const _StatusChip({required this.isCalculated});

  @override
  Widget build(BuildContext context) {
    final bg = isCalculated
        ? AppColors.success.withOpacity(0.12)
        : AppColors.warning.withOpacity(0.12);
    final fg = isCalculated ? AppColors.success : AppColors.warning;
    final text = isCalculated ? 'Done' : 'Pending';

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: fg.withOpacity(0.35)),
      ),
      child: Row(
        children: [
          Icon(
            isCalculated ? Icons.check_circle_rounded : Icons.hourglass_bottom_rounded,
            size: 16,
            color: fg,
          ),
          const SizedBox(width: 6),
          Text(
            text,
            style: TextStyle(
              color: fg,
              fontWeight: FontWeight.w800,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}

class _InfoPill extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoPill({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.borderLight),
      ),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: AppColors.primary.withOpacity(0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: AppColors.primary, size: 20),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  value,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}