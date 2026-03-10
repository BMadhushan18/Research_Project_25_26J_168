"""Fix upload_building_plan_screen.dart:
1. Add missing _contourResultBytes and _houghResultBytes state vars
2. Replace _buildGeminiResultView with _buildAnalysisResultView
"""

with open('lib/screens/upload_building_plan_screen.dart', 'rb') as f:
    data = f.read()

# ── Fix 1: add missing state variables after _pipelineStep ──────────────────
old1 = b'  int _pipelineStep = 0;\r\n\r\n  Map<String, dynamic>? _wallingResult;'
new1 = (
    b'  int _pipelineStep = 0;\r\n\r\n'
    b'  List<Uint8List> _contourResultBytes = [];\r\n'
    b'  List<Uint8List> _houghResultBytes = [];\r\n\r\n'
    b'  Map<String, dynamic>? _wallingResult;'
)
if old1 in data:
    data = data.replace(old1, new1, 1)
    print('Fix 1 OK: state vars added')
else:
    print('Fix 1 FAILED')

# ── Fix 2: replace _buildGeminiResultView with _buildAnalysisResultView ──────
# Find the marker bytes for the old method header
marker_start = data.find(b'_buildGeminiResultView()')
if marker_start == -1:
    print('Fix 2 FAILED: _buildGeminiResultView not found')
else:
    # Find widget declaration start
    decl_start = data.rfind(b'\r\n  Widget _buildGeminiResultView', 0, marker_start)
    if decl_start == -1:
        print('Fix 2 FAILED: decl start not found')
    else:
        decl_start += 2  # skip leading \r\n

        # Find the closing } of the method - count brace depth
        brace_depth = 0
        i = marker_start
        method_end = -1
        while i < len(data):
            c = data[i:i+1]
            if c == b'{':
                brace_depth += 1
            elif c == b'}':
                brace_depth -= 1
                if brace_depth == 0:
                    method_end = i + 1
                    break
            i += 1

        if method_end == -1:
            print('Fix 2 FAILED: could not find method end')
        else:
            old_method = data[decl_start:method_end]
            new_method = (
                b'  Widget _buildAnalysisResultView({\r\n'
                b"    required int step,\r\n"
                b"    required String label,\r\n"
                b"    required IconData icon,\r\n"
                b"    required Color color,\r\n"
                b"    required Map<String, dynamic>? result,\r\n"
                b"    required String nextLabel,\r\n"
                b"    required VoidCallback onNext,\r\n"
                b"  }) {\r\n"
                b"    final prettyJson = const JsonEncoder.withIndent('  ').convert(result ?? {});\r\n"
                b"\r\n"
                b"    return Column(\r\n"
                b"      crossAxisAlignment: CrossAxisAlignment.stretch,\r\n"
                b"      children: [\r\n"
                b"        _PipelineProgress(currentStep: step),\r\n"
                b"        Container(\r\n"
                b"          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),\r\n"
                b"          color: color.withAlpha(20),\r\n"
                b"          child: Row(\r\n"
                b"            children: [\r\n"
                b"              Icon(icon, color: color, size: 20),\r\n"
                b"              const SizedBox(width: 8),\r\n"
                b"              Text(\r\n"
                b"                label,\r\n"
                b"                style: TextStyle(\r\n"
                b"                  fontSize: 16,\r\n"
                b"                  fontWeight: FontWeight.bold,\r\n"
                b"                  color: color,\r\n"
                b"                ),\r\n"
                b"              ),\r\n"
                b"            ],\r\n"
                b"          ),\r\n"
                b"        ),\r\n"
                b"        Expanded(\r\n"
                b"          child: Container(\r\n"
                b"            margin: const EdgeInsets.all(12),\r\n"
                b"            decoration: BoxDecoration(\r\n"
                b"              color: const Color(0xFF0D1117),\r\n"
                b"              borderRadius: BorderRadius.circular(12),\r\n"
                b"              border: Border.all(color: color.withAlpha(60)),\r\n"
                b"            ),\r\n"
                b"            child: SingleChildScrollView(\r\n"
                b"              padding: const EdgeInsets.all(14),\r\n"
                b"              child: SelectableText(\r\n"
                b"                prettyJson,\r\n"
                b"                style: const TextStyle(\r\n"
                b"                  fontFamily: 'monospace',\r\n"
                b"                  fontSize: 11.5,\r\n"
                b"                  color: Color(0xFF79C0FF),\r\n"
                b"                  height: 1.5,\r\n"
                b"                ),\r\n"
                b"              ),\r\n"
                b"            ),\r\n"
                b"          ),\r\n"
                b"        ),\r\n"
                b"        Padding(\r\n"
                b"          padding: const EdgeInsets.fromLTRB(12, 0, 12, 16),\r\n"
                b"          child: ElevatedButton.icon(\r\n"
                b"            onPressed: onNext,\r\n"
                b"            icon: Icon(step < 5 ? Icons.arrow_forward : Icons.save_outlined),\r\n"
                b"            label: Text(\r\n"
                b"              nextLabel,\r\n"
                b"              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold),\r\n"
                b"            ),\r\n"
                b"            style: ElevatedButton.styleFrom(\r\n"
                b"              backgroundColor: color,\r\n"
                b"              foregroundColor: Colors.white,\r\n"
                b"              padding: const EdgeInsets.symmetric(vertical: 14),\r\n"
                b"              shape: RoundedRectangleBorder(\r\n"
                b"                  borderRadius: BorderRadius.circular(10)),\r\n"
                b"            ),\r\n"
                b"          ),\r\n"
                b"        ),\r\n"
                b"      ],\r\n"
                b"    );\r\n"
                b"  }"
            )
            data = data[:decl_start] + new_method + data[method_end:]
            print(f'Fix 2 OK: replaced _buildGeminiResultView ({len(old_method)} bytes) with _buildAnalysisResultView ({len(new_method)} bytes)')

with open('lib/screens/upload_building_plan_screen.dart', 'wb') as f:
    f.write(data)
print('File written.')
