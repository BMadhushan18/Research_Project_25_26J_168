with open('lib/screens/upload_building_plan_screen.dart', 'rb') as f:
    data = f.read()

# 1. Fix contour result view button
old_btn = (
    b'onPressed: _applyHoughTransform,\r\n'
    b'            icon: const Icon(Icons.timeline),\r\n'
    b"            label: const Text(\r\n              'Apply Hough Line Transform',\r\n"
    b'              style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),\r\n'
    b'            ),\r\n'
    b'            style: ElevatedButton.styleFrom(\r\n'
    b'              backgroundColor: const Color(0xFF1565C0),\r\n'
)
new_btn = (
    b'onPressed: _sendToGemini,\r\n'
    b'            icon: const Icon(Icons.auto_awesome),\r\n'
    b"            label: const Text(\r\n              'Send to Gemini - Extract Measurements',\r\n"
    b'              style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),\r\n'
    b'            ),\r\n'
    b'            style: ElevatedButton.styleFrom(\r\n'
    b'              backgroundColor: const Color(0xFF6A1B9A),\r\n'
)
if old_btn in data:
    data = data.replace(old_btn, new_btn, 1)
    print('button OK')
else:
    print('button NOT FOUND')

# 2. Fix step < 5 -> step < 4 in _buildAnalysisResultView
data = data.replace(
    b'icon: Icon(step < 5 ? Icons.arrow_forward',
    b'icon: Icon(step < 4 ? Icons.arrow_forward',
    1,
)
print('step<5 patched')

# 3. Fix PipelineProgress steps and colors
old_prog = (
    b"const steps = ['Upload', 'Contour', 'Hough', 'Walls', 'Frame', 'Finish', 'Done'];\r\n"
    b'    const colors = [\r\n'
    b'      AppColors.primary,\r\n'
    b'      Color(0xFF2E7D32),\r\n'
    b'      Color(0xFF1565C0),\r\n'
    b'      Color(0xFF6A1B9A),\r\n'
    b'      Color(0xFF1565C0),\r\n'
    b'      Color(0xFF2E7D32),\r\n'
    b'      Color(0xFF2E7D32),\r\n'
    b'    ];\r\n'
)
new_prog = (
    b"const steps = ['Upload', 'Contour', 'Walls', 'Frame', 'Finish', 'Done'];\r\n"
    b'    const colors = [\r\n'
    b'      AppColors.primary,\r\n'
    b'      Color(0xFF2E7D32),\r\n'
    b'      Color(0xFF6A1B9A),\r\n'
    b'      Color(0xFF1565C0),\r\n'
    b'      Color(0xFF2E7D32),\r\n'
    b'      Color(0xFF2E7D32),\r\n'
    b'    ];\r\n'
)
if old_prog in data:
    data = data.replace(old_prog, new_prog, 1)
    print('progress OK')
else:
    print('progress NOT FOUND')

with open('lib/screens/upload_building_plan_screen.dart', 'wb') as f:
    f.write(data)
print('Done.')
