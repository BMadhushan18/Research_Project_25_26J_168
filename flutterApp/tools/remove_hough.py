with open('lib/screens/upload_building_plan_screen.dart', 'rb') as f:
    data = f.read()

# ── 1. Remove _applyHoughTransform() method + its section comment ───────────
hough_fn = data.find(b'Future<void> _applyHoughTransform()')
send_fn  = data.find(b'Future<void> _sendToGemini()')

step2_start = data.rfind(b'\r\n  // ', 0, hough_fn)   # \r\n  // Step 2 – Hough
step3_start = data.rfind(b'\r\n  // ', 0, send_fn)    # \r\n  // Step 3 – Gemini

assert step2_start > 0 and step3_start > step2_start, 'Anchor 1 failed'
data = data[:step2_start] + data[step3_start:]
print(f'Removed _applyHoughTransform: cut [{step2_start},{step3_start})')

# ── 2. Remove _buildHoughResultView() method + its section comment ──────────
build_hough_fn    = data.find(b'Widget _buildHoughResultView()')
build_analysis_fn = data.find(b'Widget _buildAnalysisResultView(')

step2_ui_start = data.rfind(b'\r\n  // ', 0, build_hough_fn)
step3_ui_start = data.rfind(b'\r\n  // ', 0, build_analysis_fn)

assert step2_ui_start > 0 and step3_ui_start > step2_ui_start, 'Anchor 2 failed'
data = data[:step2_ui_start] + data[step3_ui_start:]
print(f'Removed _buildHoughResultView: cut [{step2_ui_start},{step3_ui_start})')

# ── 3. Fix upload info text: remove Hough mention ────────────────────────────
info_start = data.find(b"'Contour Detection ")
line_end   = data.find(b"then sent to '\r\n", info_start) + len(b"then sent to '\r\n")
assert info_start > 0 and line_end > info_start, 'Anchor 3 failed'
data = data[:info_start] + b"'Contour Detection, then sent to '\r\n" + data[line_end:]
print('Fixed upload info text')

with open('lib/screens/upload_building_plan_screen.dart', 'wb') as f:
    f.write(data)
print('Done.')
