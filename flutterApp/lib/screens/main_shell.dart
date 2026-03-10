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

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex.clamp(0, 3);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<GeminiProvider>().loadKey();
    });
  }

  @override
  Widget build(BuildContext context) {
    final selectedProject = context.watch<MongoProjectProvider>().currentProject;

    final pages = <Widget>[
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
    );
  }
}
 
