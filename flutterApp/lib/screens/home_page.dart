import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/mongo_project_provider.dart';
import '../models/project/project_model.dart';
import '../utils/constants.dart';
import 'login_screen.dart';
import 'material_estimate_screen.dart';
import 'wood_detection_screen.dart';
import 'cost_estimation_screen.dart';
import 'time_estimation/time_estimate_screen.dart';
import 'machine_management_screen.dart';
import 'create_project_flow.dart';
import 'projects/projects_screen.dart';
import 'build_project_screen.dart';
import 'settings_gemini.dart';
import 'boq_screen.dart';
import 'progress_overview_screen.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage>
    with SingleTickerProviderStateMixin {
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 1200),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
    _animationController.forward();

    // Auto-fetch all projects when Home Page loads
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<MongoProjectProvider>(context, listen: false).listenProjects();
    });
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  void _navigateToBuildProject() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const BuildProjectScreen()),
    );
  }

  void _navigateToCreateProjectFlow() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => CreateProjectFlow()),
    );
  }

  void _logout() {
    Navigator.of(context, rootNavigator: true).pushAndRemoveUntil(
      MaterialPageRoute(builder: (context) => const LoginScreen()),
      (route) => false,
    );
  }

  void _showNotImplemented() {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text('This feature is not yet implemented'),
        backgroundColor: AppColors.warning,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: _scaffoldKey,
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        leading: Container(
          margin: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: AppColors.primary.withOpacity(0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: IconButton(
            icon: Icon(Icons.menu_rounded, color: AppColors.primary),
            onPressed: () => _scaffoldKey.currentState?.openDrawer(),
          ),
        ),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Smart Construction',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(
              'Management System',
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 12,
                fontWeight: FontWeight.w400,
              ),
            ),
          ],
        ),
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 16),
            child: CircleAvatar(
              backgroundColor: AppColors.primary.withOpacity(0.1),
              child: Icon(
                Icons.account_circle_rounded,
                color: AppColors.primary,
              ),
            ),
          ),
        ],
      ),
      drawer: _buildModernDrawer(context),
      body: FadeTransition(
        opacity: _fadeAnimation,
        child: RefreshIndicator(
          onRefresh: () async {
            final provider =
                Provider.of<MongoProjectProvider>(context, listen: false);
            try {
              provider.listenProjects();
            } catch (_) {}
            await Future.delayed(const Duration(milliseconds: 400));
          },
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 110),
            child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Project Switcher
              _buildProjectSelector(context),
              const SizedBox(height: 20),

              // Welcome Header
              _buildWelcomeHeader(),

              const SizedBox(height: 32),

              // Main Features
              Text(
                'Main Features',
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),

              _buildFeaturesGrid(),

              const SizedBox(height: 32),

              // Additional Tools
              Text(
                'Additional Tools',
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),

              _buildAdditionalTools(),


            ],
          ),
        ),
      ),
    ),
  );
  }

  Widget _buildProjectSelector(BuildContext context) {
    return Consumer<MongoProjectProvider>(
      builder: (context, provider, child) {
        if (provider.loading) {
          return const Center(child: CircularProgressIndicator());
        }

        if (provider.projects.isEmpty) {
          return Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.amber.shade50,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.amber.shade200),
            ),
            child: const Row(
              children: [
                Icon(Icons.warning_amber_rounded, color: Colors.orange),
                SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'No projects found. Please create one to start.',
                    style: TextStyle(color: Colors.brown),
                  ),
                ),
              ],
            ),
          );
        }

        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.primary.withOpacity(0.2)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 10,
                offset: const Offset(0, 4),
              )
            ],
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<ProjectModel>(
              isExpanded: true,
              value: provider.projects.cast<ProjectModel?>().firstWhere(
                    (p) => p?.projectId == provider.currentProject?.projectId,
                    orElse: () => null,
                  ),
              hint: const Text('Select active project...'),
              icon: Icon(Icons.arrow_drop_down_circle, color: AppColors.primary),
              items: { for (var p in provider.projects) p.projectId: p }
                  .values.map((ProjectModel project) {
                return DropdownMenuItem<ProjectModel>(
                  value: project,
                  child: Row(
                    children: [
                      Icon(Icons.business_center,
                          size: 20, color: AppColors.primary),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          project.projectName ?? 'Unnamed Project',
                          style:
                              const TextStyle(fontWeight: FontWeight.w600),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      Text(
                        project.location ?? 'No location',
                        style: TextStyle(
                            fontSize: 12, color: Colors.grey.shade500),
                      )
                    ],
                  ),
                );
              }).toList(),
              onChanged: (ProjectModel? newValue) async {
                if (newValue == null) return;

                final provider = context.read<MongoProjectProvider>();

                // Selected project id
                final String pid = newValue.projectId;

                // Set active project in provider
                await provider.selectProject(pid);

                // Now pid is stored in provider.currentProject
                print("Selected PID = $pid");

                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Switched to ${newValue.projectName} workspace.'),
                    behavior: SnackBarBehavior.floating,
                    backgroundColor: Colors.green,
                  ),
                );
              },
            ),
          ),
        );
      },
    );
  }

  Widget _buildWelcomeHeader() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.primary, AppColors.primaryLight],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withOpacity(0.3),
            blurRadius: 15,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Icon(
                  Icons.business_rounded,
                  color: Colors.white,
                  size: 32,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Welcome Back!',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      'Ready to build something amazing?',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.9),
                        fontSize: 16,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildFeaturesGrid() {
    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 2,
      crossAxisSpacing: 16,
      mainAxisSpacing: 16,
      childAspectRatio: 0.95,
      children: [
        _buildFeatureCard(
          icon: Icons.add_box_rounded,
          title: 'Create Project',
          description: 'Start a new construction project',
          color: AppColors.primary,
          backgroundIcon: Icons.add,
          onTap: _navigateToCreateProjectFlow,
        ),
        _buildFeatureCard(
          icon: Icons.park_rounded,
          title: 'Wood Detection',
          description: 'Identify wood materials',
          color: Colors.brown,
          backgroundImage: 'AppImages/wood_detection.jpg',
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(
                builder: (context) => const WoodDetectionScreen()),
          ),
        ),
        _buildFeatureCard(
          icon: Icons.attach_money_rounded,
          title: 'Cost Estimation',
          description: 'Project budget analysis',
          color: AppColors.success,
          backgroundImage: 'AppImages/costEstimate.jpg',
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(
                builder: (context) => const CostEstimationScreen()),
          ),
        ),
        _buildFeatureCard(
          icon: Icons.calculate_rounded,
          title: 'Time Estimate',
          description: 'Project Schedule Analysis',
          color: AppColors.success,
          backgroundImage: 'AppImages/time_estimate.png',
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(
                builder: (context) => const TimeEstimateScreen()),
          ),
        ),
        _buildFeatureCard(
          icon: Icons.bar_chart_rounded,
          title: 'Progress',
          description: 'Track project progress',
          color: Colors.deepPurple,
          backgroundIcon: Icons.bar_chart,
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(
                builder: (context) => const ProgressOverviewScreen()),
          ),
        ),
      ],
    );
  }

  Widget _buildAdditionalTools() {
    return Column(
      children: [
        _buildToolCard(
          icon: Icons.receipt_long_rounded,
          title: 'BOQ Report',
          description: 'Bill of quantities — material breakdown by section',
          color: const Color(0xFF00897B),
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(builder: (context) => const BOQScreen()),
          ),
        ),
        const SizedBox(height: 12),
        _buildToolCard(
          icon: Icons.currency_rupee_rounded,
          title: 'Cost Report',
          description: 'Detailed cost estimation and budget analysis',
          color: const Color(0xFF1565C0),
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(
                builder: (context) => const CostEstimationScreen()),
          ),
        ),
        const SizedBox(height: 12),
        _buildToolCard(
          icon: Icons.precision_manufacturing_rounded,
          title: 'Machinery and Labour',
          description: 'Equipment and workforce management',
          color: const Color(0xFF6A1B9A),
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(
                builder: (context) => const MachineManagementScreen()),
          ),
        ),
      ],
    );
  }

  Widget _buildMyProjectsSection() {
    return Container(
      height: 150,
      margin: const EdgeInsets.only(top: 8),
      child: ListView(
        scrollDirection: Axis.horizontal,
        children: [
          // Create Project card
          GestureDetector(
            onTap: _navigateToCreateProjectFlow,
            child: Container(
              width: 260,
              margin: const EdgeInsets.only(right: 16),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.cardBackground,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.borderLight, width: 1),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    width: 56,
                    height: 56,
                    decoration: BoxDecoration(
                      color: AppColors.primary.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child:
                        Icon(Icons.add, color: AppColors.primary, size: 36),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Create Project',
                    style: TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Start a new construction project',
                    style: TextStyle(color: AppColors.textSecondary),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ),

          // Placeholder for existing projects (empty state)
          Container(
            width: 260,
            margin: const EdgeInsets.only(right: 16),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.cardBackground,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.borderLight, width: 1),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.folder_open,
                    color: AppColors.textSecondary, size: 36),
                const SizedBox(height: 12),
                Text(
                  'No projects yet',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Your saved projects will appear here',
                  style: TextStyle(color: AppColors.textSecondary),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFeatureCard({
    required IconData icon,
    required String title,
    required String description,
    required Color color,
    String? backgroundImage,
    IconData? backgroundIcon,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: AppColors.cardBackground,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.borderLight, width: 1),
          boxShadow: [
            BoxShadow(
              color: AppColors.cardShadow,
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
          image: backgroundImage != null
              ? DecorationImage(
                  image: AssetImage(backgroundImage),
                  fit: BoxFit.cover,
                  colorFilter: ColorFilter.mode(
                      Colors.black.withOpacity(0.22), BlendMode.darken),
                )
              : null,
        ),
        child: Stack(
          children: [
            // Background large icon (if provided)
            if (backgroundIcon != null)
              Positioned.fill(
                child: Center(
                  child: Icon(
                    backgroundIcon,
                    size: 120,
                    color: Colors.white.withOpacity(0.14),
                  ),
                ),
              ),

            // Icon at top-left
            Positioned(
              top: 16,
              left: 16,
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: Colors.white, size: 28),
              ),
            ),

            // Centered title with white backdrop
            Center(
              child: Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.9),
                  borderRadius: BorderRadius.circular(8),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.25),
                      blurRadius: 8,
                      offset: const Offset(0, 3),
                    ),
                  ],
                ),
                child: Text(
                  title,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ),

            // Description at bottom
            Positioned(
              bottom: 16,
              left: 16,
              right: 16,
              child: Text(
                description,
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 12,
                  height: 1.3,
                ),
                textAlign: TextAlign.left,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildToolCard({
    required IconData icon,
    required String title,
    required String description,
    required Color color,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.cardBackground,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.borderLight, width: 1),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: color, size: 24),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  Text(
                    description,
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
            Icon(
              Icons.arrow_forward_ios_rounded,
              color: AppColors.textHint,
              size: 16,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildModernDrawer(BuildContext context) {
    return Drawer(
      backgroundColor: AppColors.background,
      child: Column(
        children: [
          // Drawer Header
          Container(
            width: double.infinity,
            padding: const EdgeInsets.fromLTRB(20, 60, 20, 20),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [AppColors.primary, AppColors.primaryLight],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: const Icon(
                    Icons.business_rounded,
                    color: Colors.white,
                    size: 32,
                  ),
                ),
                const SizedBox(height: 16),
                const Text(
                  'Smart Construction',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Text(
                  'Management System v1.0',
                  style: TextStyle(
                    color: Colors.white70,
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ),

          // Menu Items
          Expanded(
            child: ListView(
              padding: const EdgeInsets.symmetric(vertical: 8),
              children: [
                _buildDrawerItem(
                  icon: Icons.home_rounded,
                  title: 'Home',
                  onTap: () => Navigator.pop(context),
                ),
                _buildDrawerItem(
                  icon: Icons.add_box_rounded,
                  title: 'Create Project',
                  color: AppColors.primary,
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (context) => CreateProjectFlow()),
                    );
                  },
                ),
                _buildDrawerItem(
                  icon: Icons.folder_open_rounded,
                  title: 'My Projects',
                  color: AppColors.primary,
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (context) => const ProjectsScreen()),
                    );
                  },
                ),
                const Divider(color: AppColors.borderLight),
                _buildDrawerItem(
                  icon: Icons.settings_rounded,
                  title: 'Settings',
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.push(context, MaterialPageRoute(builder: (_) => const SettingsScreen()));
                  },
                ),
                _buildDrawerItem(
                  icon: Icons.info_outline_rounded,
                  title: 'About',
                  onTap: () {
                    Navigator.pop(context);
                    _showAboutDialog();
                  },
                ),
              ],
            ),
          ),

          // Logout
          Container(
            margin: const EdgeInsets.all(16),
            child: _buildDrawerItem(
              icon: Icons.logout_rounded,
              title: 'Logout',
              color: AppColors.error,
              onTap: _logout,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDrawerItem({
    required IconData icon,
    required String title,
    Color? color,
    required VoidCallback onTap,
  }) {
    final itemColor = color ?? AppColors.textSecondary;

    return ListTile(
      leading: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: itemColor.withOpacity(0.1),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Icon(icon, color: itemColor, size: 20),
      ),
      title: Text(
        title,
        style: TextStyle(
          color: AppColors.textPrimary,
          fontSize: 16,
          fontWeight: FontWeight.w500,
        ),
      ),
      onTap: onTap,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 20),
    );
  }

  void _showAboutDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.cardBackground,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Row(
          children: [
            Icon(Icons.info_outline_rounded, color: AppColors.primary),
            const SizedBox(width: 12),
            Text(
              'About',
              style: TextStyle(color: AppColors.textPrimary),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Smart Construction Management System',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Version 1.0.0',
              style: TextStyle(color: AppColors.textSecondary),
            ),
            const SizedBox(height: 16),
            Text(
              'Complete construction project management solution with cost estimation, material tracking, logistics, and project analysis.',
              style: TextStyle(
                color: AppColors.textSecondary,
                height: 1.4,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            style: TextButton.styleFrom(foregroundColor: AppColors.primary),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }
}
