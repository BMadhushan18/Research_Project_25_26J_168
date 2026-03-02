import 'package:flutter/material.dart';
import '../utils/constants.dart';

class WoodDetectionScreen extends StatelessWidget {
  const WoodDetectionScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Wood Detection'),
        backgroundColor: AppColors.primary,
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: const [
            Icon(Icons.park, size: 100, color: Colors.brown),
            SizedBox(height: 24),
            Text(
              'Wood Detection Module',
              style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Colors.white),
            ),
            SizedBox(height: 16),
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 40),
              child: Text(
                'AI-powered wood type detection and analysis',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 16, color: Colors.white70),
              ),
            ),
            SizedBox(height: 32),
            Text(
              'Coming Soon',
              style: TextStyle(fontSize: 18, color: Colors.orange),
            ),
          ],
        ),
      ),
    );
  }
}
