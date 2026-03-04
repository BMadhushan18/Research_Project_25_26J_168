import 'package:flutter/material.dart';
import '../../utils/constants.dart';
import 'phase_wise_duration_screen.dart';

class EstimationResultScreen extends StatelessWidget {
  final int durationDays;

  final String durationText;

  const EstimationResultScreen({
    super.key,
    required this.durationDays,
    required this.durationText,
  });

  List<String> _durationLines(String text) {
    final tokens = text.trim().split(RegExp(r'\s+'));
    final lines = <String>[];

    for (int i = 0; i < tokens.length; i += 2) {
      final first = tokens[i];
      final second = (i + 1 < tokens.length) ? tokens[i + 1] : '';
      lines.add(second.isEmpty ? first : '$first $second');
    }

    return lines;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Total Duration'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: Column(
        children: [
          _buildTopBanner(),
          Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              children: [
                _buildDurationCard(),
                const SizedBox(height: 16),

                // ✅ show total days clearly (no decimals)
                Text(
                  'Total: $durationDays day${durationDays == 1 ? '' : 's'}',
                  style: TextStyle(
                    fontSize: 14,
                    color: AppColors.textSecondary,
                    fontWeight: FontWeight.w500,
                  ),
                ),

                const SizedBox(height: 30),
                Text(
                  "Do you want to see phase wise duration?",
                  style: TextStyle(
                    fontSize: 18,
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 20),
                _buildPhaseWiseButton(context),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTopBanner() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 20),
      decoration: BoxDecoration(
        color: AppColors.primary,
        borderRadius: const BorderRadius.only(
          bottomLeft: Radius.circular(30),
          bottomRight: Radius.circular(30),
        ),
      ),
      child: const Icon(
        Icons.check_circle_outline_rounded,
        color: Colors.white,
        size: 80,
      ),
    );
  }

  Widget _buildDurationCard() {
    final lines = _durationLines(durationText);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(26),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: AppColors.cardShadow,
            blurRadius: 15,
            offset: const Offset(0, 10),
          ),
        ],
        border: Border.all(color: AppColors.primary.withOpacity(0.2)),
      ),
      child: Column(
        children: [
          Text(
            'Estimated Total Duration',
            style: TextStyle(
              fontSize: 16,
              color: AppColors.textSecondary,
              letterSpacing: 1.2,
            ),
          ),
          const SizedBox(height: 14),

          Column(
            mainAxisSize: MainAxisSize.min,
            children: lines
                .map(
                  (l) => Text(
                    l,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 34,
                      fontWeight: FontWeight.bold,
                      color: AppColors.primary,
                      height: 1.1,
                    ),
                  ),
                )
                .toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildPhaseWiseButton(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 60,
      child: ElevatedButton.icon(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => const PhaseWiseDurationScreen(),
            ),
          );
        },
        icon: const Icon(Icons.timeline_rounded),
        label: const Text(
          'Phase Wise Duration',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color.fromARGB(255, 231, 80, 29),
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(15),
          ),
          elevation: 5,
        ),
      ),
    );
  }
}