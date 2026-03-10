import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import '../providers/mongo_project_provider.dart';
import '../utils/constants.dart';
import 'home_page.dart';
import 'view_3d_screen.dart';
import 'project_search_screen.dart';
import 'project_progress/track_progress_screen.dart';

class MainShell extends StatefulWidget {
  final int initialIndex;

  const MainShell({super.key, this.initialIndex = 0});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell>
    with SingleTickerProviderStateMixin {
  late int _currentIndex;

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex.clamp(0, 3);
  }

  // Map bottom-nav bar position → page index
  // bar positions: 0=Home, 1=3D, 2=Camera(action), 3=Search, 4=Progress
  int _pageIndexFromBar(int barPos) {
    if (barPos < 2) return barPos;
    return barPos - 1; // skip camera slot
  }

  Future<void> _openCamera() async {
    HapticFeedback.mediumImpact();
    try {
      final picker = ImagePicker();
      await picker.pickImage(source: ImageSource.camera, imageQuality: 90);
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('Camera permission required.'),
            backgroundColor: AppColors.primary,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10)),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<MongoProjectProvider>();
    final selectedProject = provider.currentProject;

    // Pages mapped to bottom nav: 0=Home, 1=3D, 2=Search, 3=Progress
    // Index 2 in the bar (camera) is an ACTION, not a page.
    final pages = [
      const HomePage(),
      const View3DScreen(),
      const ProjectSearchScreen(),
      TrackProgressScreen(
        pid: selectedProject?.projectId,
        projectName: selectedProject?.projectName,
        location: selectedProject?.location,
      ),
    ];

    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: pages,
      ),
      extendBody: true,
      bottomNavigationBar: _BottomNavBar(
        currentPageIndex: _currentIndex,
        onItemTap: (barPos) {
          if (barPos == 2) {
            _openCamera();
          } else {
            final pi = _pageIndexFromBar(barPos);
            if (pi != _currentIndex) {
              HapticFeedback.selectionClick();
              setState(() => _currentIndex = pi);
            }
          }
        },
      ),
    );
  }
}

// ─── Custom Bottom Nav Bar ────────────────────────────────────────────────────
class _BottomNavBar extends StatelessWidget {
  final int currentPageIndex;
  final ValueChanged<int> onItemTap;

  const _BottomNavBar({
    required this.currentPageIndex,
    required this.onItemTap,
  });

  // bar position → page index (camera is action so -1)
  bool _isSelected(int barPos) {
    if (barPos == 2) return false; // camera never "selected"
    final pi = barPos < 2 ? barPos : barPos - 1;
    return pi == currentPageIndex;
  }

  @override
  Widget build(BuildContext context) {
    final items = [
      _NavItem(icon: Icons.home_rounded, label: 'Home'),
      _NavItem(icon: Icons.view_in_ar_rounded, label: '3D View'),
      _NavItem(icon: Icons.camera_alt_rounded, label: 'Camera', isCenter: true),
      _NavItem(icon: Icons.search_rounded, label: 'Projects'),
      _NavItem(icon: Icons.bar_chart_rounded, label: 'Progress'),
    ];

    return Container(
      margin: const EdgeInsets.fromLTRB(16, 0, 16, 14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(30),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.12),
            blurRadius: 20,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: List.generate(items.length, (i) {
              final item = items[i];
              final selected = _isSelected(i);

              if (item.isCenter) {
                // ── Raised camera button ──────────────────────────────────
                return GestureDetector(
                  onTap: () => onItemTap(i),
                  child: Transform.translate(
                    offset: const Offset(0, -18),
                    child: Container(
                      width: 58,
                      height: 58,
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [
                            AppColors.primary,
                            AppColors.primaryLight
                          ],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: AppColors.primary.withOpacity(0.45),
                            blurRadius: 14,
                            offset: const Offset(0, 5),
                          ),
                        ],
                      ),
                      child: const Icon(
                        Icons.camera_alt_rounded,
                        color: Colors.white,
                        size: 28,
                      ),
                    ),
                  ),
                );
              }

              // ── Regular nav item ─────────────────────────────────────────
              return GestureDetector(
                onTap: () => onItemTap(i),
                behavior: HitTestBehavior.opaque,
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  padding: const EdgeInsets.symmetric(
                      horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: selected
                        ? AppColors.primary.withOpacity(0.1)
                        : Colors.transparent,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      AnimatedSwitcher(
                        duration: const Duration(milliseconds: 200),
                        child: Icon(
                          item.icon,
                          key: ValueKey(selected),
                          size: 24,
                          color: selected
                              ? AppColors.primary
                              : AppColors.textHint,
                        ),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        item.label,
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: selected
                              ? FontWeight.w600
                              : FontWeight.w400,
                          color: selected
                              ? AppColors.primary
                              : AppColors.textHint,
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }),
          ),
        ),
      ),
    );
  }
}

class _NavItem {
  final IconData icon;
  final String label;
  final bool isCenter;
  const _NavItem(
      {required this.icon, required this.label, this.isCenter = false});
}
