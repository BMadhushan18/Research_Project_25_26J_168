import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
// ── MongoDB providers (active) ────────────────────────────────────────────────
import 'config/app_config.dart' as mongo_cfg;
import 'providers/mongo_auth_provider.dart';
import 'providers/mongo_project_provider.dart';
import 'screens/login_screen.dart';
import 'screens/main_shell.dart';
import 'utils/constants.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  debugPrint('MongoDB mode active: ${mongo_cfg.AppConfig.baseUrl}');

  // Lock orientation to portrait
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // ── MongoDB providers ─────────────────────────────────────────────────
        ChangeNotifierProvider(create: (_) => MongoAuthProvider()),
        ChangeNotifierProvider(create: (_) => MongoProjectProvider()),
      ],
      child: MaterialApp(
        title: 'Smart Construction Manage System',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: AppColors.primary,
            brightness: Brightness.light,
          ),
          scaffoldBackgroundColor: AppColors.background,
          appBarTheme: AppBarTheme(
            backgroundColor: AppColors.background,
            foregroundColor: AppColors.textPrimary,
            elevation: 0,
            centerTitle: true,
          ),
          cardTheme: CardThemeData(
            color: AppColors.surface,
            elevation: 2,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
          ),
          elevatedButtonTheme: ElevatedButtonThemeData(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            ),
          ),
          useMaterial3: true,
        ),
        // ── MongoDB auth routing ───────────────────────────────────────────
        home: Consumer<MongoAuthProvider>(
          builder: (context, auth, _) {
            if (!auth.initialized) {
              return const Scaffold(
                body: Center(child: CircularProgressIndicator()),
              );
            }
            if (auth.isAuthenticated) {
              return const MainShell();
            }
            return const LoginScreen();
          },
        ),
      ),
    );
  }
}
