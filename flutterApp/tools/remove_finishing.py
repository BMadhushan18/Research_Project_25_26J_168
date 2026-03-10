with open('lib/screens/upload_building_plan_screen.dart', 'r', encoding='utf-8', errors='replace') as f:
    d = f.read()

# ── 1. Remove _callFinishingMeasurements() method (Step 5 comment → Step 6 comment) ──
step5_start = d.find('\n  // ─── Step 5 — Finishing')
step6_start = d.find('\n  // ─── Step 6 — Save')
assert step5_start > 0 and step6_start > step5_start, f'anchors failed: {step5_start} {step6_start}'
d = d[:step5_start] + d[step6_start:]
print('Removed _callFinishingMeasurements')

# ── 2. Remove _finishingResult state var ──
d = d.replace('  Map<String, dynamic>? _finishingResult;\n', '', 1)
print('Removed _finishingResult state var')

# ── 3. Remove the "Continue - Finishing" nextLabel and whole case 4 from build switch ──
# case 4 is the finishing case
old_case4 = (
    "        4 => _buildAnalysisResultView(\n"
    "              step: 4,\n"
    "              label: 'Finishing Measurements',\n"
    "              icon: Icons.brush_outlined,\n"
    "              color: const Color(0xFF2E7D32),\n"
    "              result: _finishingResult,\n"
    "              nextLabel: 'Save & Complete',\n"
    "              onNext: _saveAndComplete,\n"
    "            ),\n"
    "        5 => _buildSuccessView(),"
)
new_case4 = (
    "        4 => _buildSuccessView(),"
)
if old_case4 in d:
    d = d.replace(old_case4, new_case4, 1)
    print('Updated build switch: removed finishing case 4')
else:
    print('build switch case 4 NOT FOUND')

# ── 4. Fix SF nextLabel from "Continue - Finishing" to "Save & Complete" ──
d = d.replace("nextLabel: 'Continue - Finishing',", "nextLabel: 'Save & Complete',", 1)
d = d.replace("onNext: _callFinishingMeasurements,", "onNext: _saveAndComplete,", 1)
print('Updated SF nextLabel and onNext')

# ── 5. Fix pipeline step: SF was setting step 3, save sets step 4 (was 5) ──
# The _saveAndComplete sets _pipelineStep = 5; needs to be 4
d = d.replace(
    "        _pipelineStep = 5;\n        _loading = false;\n        _status = '';",
    "        _pipelineStep = 4;\n        _loading = false;\n        _status = '';",
    1
)
print('Updated _saveAndComplete pipeline step 5->4')

# ── 6. Remove save call to postFinishing ──
old_finish_save = (
    "\n      if (_finishingResult != null) {\n"
    "        setState(() => _status = 'Saving finishing data...');\n"
    "        final finishing = _finishingResult!['finishing'];\n"
    "        await api.postFinishing(\n"
    "          widget.projectId,\n"
    "          finishing is Map<String, dynamic> ? finishing : _finishingResult!,\n"
    "        );\n"
    "      }\n"
)
if old_finish_save in d:
    d = d.replace(old_finish_save, '\n', 1)
    print('Removed postFinishing call')
else:
    print('postFinishing save block NOT FOUND')

# ── 7. Update PipelineProgress steps array ──
d = d.replace(
    "const steps = ['Upload', 'Contour', 'Walls', 'Frame', 'Finish', 'Done'];",
    "const steps = ['Upload', 'Contour', 'Walls', 'Frame', 'Done'];",
    1
)
# Fix colors array (remove one color - the Finish color 0xFF2E7D32)
old_colors = (
    "    const colors = [\n"
    "      AppColors.primary,\n"
    "      Color(0xFF2E7D32),\n"
    "      Color(0xFF6A1B9A),\n"
    "      Color(0xFF1565C0),\n"
    "      Color(0xFF2E7D32),\n"
    "      Color(0xFF2E7D32),\n"
    "    ];\n"
)
new_colors = (
    "    const colors = [\n"
    "      AppColors.primary,\n"
    "      Color(0xFF2E7D32),\n"
    "      Color(0xFF6A1B9A),\n"
    "      Color(0xFF1565C0),\n"
    "      Color(0xFF2E7D32),\n"
    "    ];\n"
)
if old_colors in d:
    d = d.replace(old_colors, new_colors, 1)
    print('Updated PipelineProgress colors')
else:
    print('PipelineProgress colors NOT FOUND')

print('Steps updated')

# ── 8. Update step comment at top of file (pipeline steps comments) ──
old_comment = (
    "  // Pipeline steps:\n"
    "  //   0 = upload (pick images)\n"
    "  //   1 = contour applied\n"
    "  //   2 = walling extracted\n"
    "  //   3 = structural frame extracted\n"
    "  //   4 = finishing extracted\n"
    "  //   5 = saved (success)\n"
)
new_comment = (
    "  // Pipeline steps:\n"
    "  //   0 = upload (pick images)\n"
    "  //   1 = contour applied\n"
    "  //   2 = walling extracted\n"
    "  //   3 = structural frame extracted\n"
    "  //   4 = saved (success)\n"
)
d = d.replace(old_comment, new_comment, 1)
print('Updated pipeline step comments')

# ── 9. Remove _sfRawText (no longer needed for multi-turn finishing) ── keep it for SF itself
# Actually _sfRawText is used in _generate3dInBackground - don't remove it

with open('lib/screens/upload_building_plan_screen.dart', 'w', encoding='utf-8') as f:
    f.write(d)
print('Done.')
