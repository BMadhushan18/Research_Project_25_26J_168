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
import 'home_page.dart';
import 'view_3d_screen.dart';
import 'project_search_screen.dart';
import 'progress_overview_screen.dart';
import 'settings_gemini.dart';
import '../utils/constants.dart';
import 'package:provider/provider.dart';
import '../providers/gemini_provider.dart';

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
class _MainShellState extends State<MainShell> {
  int _currentIndex = 0;

  // One navigator key per tab — keeps nav stack alive inside each tab.
  final List<GlobalKey<NavigatorState>> _navKeys = [
    GlobalKey<NavigatorState>(),
    GlobalKey<NavigatorState>(),
    GlobalKey<NavigatorState>(),
    GlobalKey<NavigatorState>(),
  ];

  // Root widget for each tab.
  static const List<Widget> _roots = [
    HomePage(),
    View3DScreen(),
    ProjectSearchScreen(),
    ProgressOverviewScreen(),
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      try {
        final prov = Provider.of<GeminiProvider>(context, listen: false);
        prov.loadKey();
      } catch (_) {
        // ignore: avoid_print
        print('GeminiProvider not available at init');
      }
    });
  }

  /// Builds a nested Navigator for a single tab.
  Widget _buildTabNavigator(int index) {
    return Navigator(
      key: _navKeys[index],
      onGenerateRoute: (_) => MaterialPageRoute(
        builder: (_) => _roots[index],
      ),
    );
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
    return PopScope(
      // Intercept Android back: pop within the current tab's navigator first.
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) {
          final nav = _navKeys[_currentIndex].currentState;
          if (nav != null && nav.canPop()) {
            nav.pop();
          }
          // If nothing to pop we swallow the back press (stay in app).
        }
      },
      child: Scaffold(
        drawer: Drawer(
          child: SafeArea(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                DrawerHeader(
                  decoration: BoxDecoration(color: AppColors.primary),
                  child: const Align(
                    alignment: Alignment.bottomLeft,
                    child: Text('Menu',
                        style: TextStyle(
                            color: Colors.white,
                            fontSize: 20,
                            fontWeight: FontWeight.w600)),
                  ),
                ),
                ListTile(
                  leading: const Icon(Icons.settings_outlined),
                  title: const Text('Settings'),
                  onTap: () {
                    Navigator.of(context).pop(); // close drawer
                    // Push Settings into the current tab's navigator.
                    _navKeys[_currentIndex].currentState?.push(
                      MaterialPageRoute(
                          builder: (_) => const SettingsScreen()),
                    );
                  },
                ),
                const Divider(),
              ],
            ),
          ),
        ),
        body: IndexedStack(
          index: _currentIndex,
          children: List.generate(4, _buildTabNavigator),
        ),
        bottomNavigationBar: SafeArea(
          bottom: true,
          child: _buildBottomNav(),
        ),
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

  Widget _buildBottomNav() {
    return Container(
      decoration: BoxDecoration(
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 20,
            offset: const Offset(0, -4),
          ),
        ],
      ),
      child: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (i) {
          if (i == _currentIndex) {
            // Tapping the active tab pops back to its root.
            _navKeys[i].currentState?.popUntil((r) => r.isFirst);
          } else {
            setState(() => _currentIndex = i);
          }
        },
        type: BottomNavigationBarType.fixed,
        backgroundColor: Colors.white,
        selectedItemColor: AppColors.primary,
        unselectedItemColor: AppColors.textSecondary,
        selectedLabelStyle:
            const TextStyle(fontWeight: FontWeight.w600, fontSize: 11),
        unselectedLabelStyle: const TextStyle(fontSize: 11),
        elevation: 0,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined),
            activeIcon: Icon(Icons.home_rounded),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.view_in_ar_outlined),
            activeIcon: Icon(Icons.view_in_ar_rounded),
            label: '3D View',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.search_outlined),
            activeIcon: Icon(Icons.search_rounded),
            label: 'Search',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.bar_chart_outlined),
            activeIcon: Icon(Icons.bar_chart_rounded),
            label: 'Progress',
          ),
        ],
      ),
    );
  }
}
