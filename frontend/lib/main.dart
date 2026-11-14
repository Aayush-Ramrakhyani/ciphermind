/*
 * CipherMind — Intelligent Autonomous Cryptanalysis Platform
 * Flutter application entry point.
 */

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/theme.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const ProviderScope(child: CipherMindApp()));
}

class CipherMindApp extends StatelessWidget {
  const CipherMindApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CipherMind',
      theme: AppTheme.dark,
      debugShowCheckedModeBanner: false,
      home: const HomeScreen(),
    );
  }
}
