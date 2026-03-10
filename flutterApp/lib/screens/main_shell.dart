import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/gemini_provider.dart';
import '../providers/mongo_project_provider.dart';
import '../utils/constants.dart';
import 'home_page.dart';
import 'project_progress/track_progress_screen.dart';
import 'project_search_screen.dart';
import 'view_3d_screen.dart';

class MainShell extends StatefulWidget {
  final int initialIndex;

  const MainShell({super.key, this.initialIndex = 0});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  late int _currentIndex;

  // Each tab has its own navigator so the bottom bar stays visible
  // when screens are pushed inside a tab.
  final List<GlobalKey<NavigatorState>> _navigatorKeys = [
    GlobalKey<NavigatorState>(),
    GlobalKey<NavigatorState>(),
    GlobalKey<NavigatorState>(),
    GlobalKey<NavigatorState>(),
  ];

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex.clamp(0, 3);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<GeminiProvider>().loadKey();
    });
  }

  /// Pop the active tab's navigator; if at its root, let the system handle it.
  bool _onBackPressed() {
    final nav = _navigatorKeys[_currentIndex].currentState;
    if (nav != null && nav.canPop()) {
      nav.pop();
      return true; // consumed
    }
    return false; // let OS handle (exit)
  }

  Widget _tabNavigator(int index, Widget Function(BuildContext) builder) {
    return Navigator(
      key: _navigatorKeys[index],
      onGenerateRoute: (settings) => MaterialPageRoute(
        builder: builder,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      // Never auto-pop the shell; we handle it manually.
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) _onBackPressed();
      },
      child: Scaffold(
        body: IndexedStack(
          index: _currentIndex,
          children: [
            _tabNavigator(0, (_) => const HomePage()),
            _tabNavigator(1, (_) => const View3DScreen()),
            _tabNavigator(2, (_) => const ProjectSearchScreen()),
            _tabNavigator(3, (ctx) {
              final sp =
                  ctx.watch<MongoProjectProvider>().currentProject;
              return TrackProgressScreen(
                pid: sp?.projectId,
                projectName: sp?.projectName,
                location: sp?.location,
              );
            }),
          ],
        ),
        bottomNavigationBar: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (index) {
            if (index == _currentIndex) return;
            setState(() => _currentIndex = index);
          },
          type: BottomNavigationBarType.fixed,
          backgroundColor: Colors.white,
          selectedItemColor: AppColors.primary,
          unselectedItemColor: AppColors.textSecondary,
          selectedLabelStyle: const TextStyle(
            fontWeight: FontWeight.w600,
            fontSize: 11,
          ),
          unselectedLabelStyle: const TextStyle(fontSize: 11),
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
              label: 'Projects',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.bar_chart_outlined),
              activeIcon: Icon(Icons.bar_chart_rounded),
              label: 'Progress',
            ),
          ],
        ),
      ),
    );
  }
}
 
