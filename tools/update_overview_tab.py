"""
Script to update overview_tab.dart:
1. Replace _WallingContent with new StatefulWidget version (doors/windows tables + clickable widths)
2. Replace _SFContent with StatefulWidget version (clickable column sizes)
3. Remove _FinishingContent class
4. Add _SectionLabel and _SizePickerSheet helper widgets
"""
import sys, os

TAB_PATH = os.path.join(os.path.dirname(__file__), '..', 'flutterApp',
                        'lib', 'screens', 'projects', 'tabs', 'overview_tab.dart')
TAB_PATH = os.path.normpath(TAB_PATH)

with open(TAB_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# ─────────────────────────────────────────────────────────────────────────────
# NEW _WallingContent  (StatefulWidget — walls table with clickable widths,
#                       plus doors and windows schedule tables)
# ─────────────────────────────────────────────────────────────────────────────
NEW_WALLING = r"""//  Walling Content

class _WallingContent extends StatefulWidget {
  final Map<String, dynamic> raw;
  final String floor;
  final Map<String, dynamic>? wallingData;
  const _WallingContent({
    required this.raw,
    required this.floor,
    this.wallingData,
  });

  @override
  State<_WallingContent> createState() => _WallingContentState();
}

class _WallingContentState extends State<_WallingContent> {
  // wall key -> user-selected width override
  final Map<String, String> _widthOverrides = {};

  static const _brickSizes = [
    {'label': '115 mm  (Half brick — default)', 'value': '0.1150 m'},
    {'label': '230 mm  (Full brick)', 'value': '0.2300 m'},
    {'label': '102 mm  (4")', 'value': '0.1020 m'},
    {'label': '275 mm  (Cavity wall)', 'value': '0.2750 m'},
    {'label': '340 mm  (1.5 brick)', 'value': '0.3400 m'},
  ];

  Map<String, dynamic>? _map(dynamic v) =>
      v is Map<String, dynamic> ? v : null;

  String _fmt(dynamic v) {
    if (v == null) return '—';
    final s = v.toString().trim();
    return (s.isEmpty || s == 'null') ? '—' : s;
  }

  /// Returns the width to display: override > stored > default 115 mm
  String _wallWidth(String key, dynamic raw) {
    if (_widthOverrides.containsKey(key)) return _widthOverrides[key]!;
    final v = _fmt(raw);
    return (v == '—') ? '0.1150 m' : v;
  }

  void _pickBrickWidth(BuildContext ctx, String wallKey, String current) {
    showModalBottomSheet(
      context: ctx,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (_) => _SizePickerSheet(
        title: 'Select Wall Width  ($wallKey)',
        items: _brickSizes.map((s) => s['label']!).toList(),
        currentValue: current,
        onSelect: (idx) =>
            setState(() => _widthOverrides[wallKey] = _brickSizes[idx]['value']!),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isGround = widget.floor == 'Ground Floor';

    final wRaw = widget.wallingData != null
        ? (_map(widget.wallingData!['data']) ?? widget.wallingData!)
        : null;
    final fallbackRaw = _map(widget.raw['data']) ?? widget.raw;

    final wOutput = _map(wRaw?['output']);
    final totalWallsVal = wOutput?['totalWalls'];
    final units = _fmt(wOutput?['units']);

    final groundFloorW = _map(wRaw?['groundFloor']);
    final wallsW = _map(groundFloorW?['walls']);

    final groundFloorFb = _map(fallbackRaw['groundFloor']);
    final wallsFb = _map(groundFloorFb?['walls']);

    final walls = isGround ? (wallsW ?? wallsFb) : null;
    final totalWalls =
        totalWallsVal?.toString() ?? walls?.length.toString() ?? '—';

    final doors = _map(wRaw?['doors']);
    final windows = _map(wRaw?['windows']);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _FloorBadge(widget.floor),
        if (!isGround) ...[
          const SizedBox(height: 12),
          const _PlaceholderNote(
              'First floor walling data will appear here once extracted.'),
        ],
        if (isGround) ...[
          const SizedBox(height: 12),
          // Summary bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: const Color(0xFF2E7D32).withAlpha(12),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: const Color(0xFF2E7D32).withAlpha(40)),
            ),
            child: Row(children: [
              const Icon(Icons.crop_square_outlined,
                  size: 16, color: Color(0xFF2E7D32)),
              const SizedBox(width: 8),
              Text(
                'Total Walls: $totalWalls',
                style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF2E7D32)),
              ),
              if (units.isNotEmpty && units != '—') ...[
                const Spacer(),
                Text('Units: $units',
                    style:
                        TextStyle(fontSize: 12, color: Colors.grey.shade600)),
              ],
            ]),
          ),
          const SizedBox(height: 16),

          // ── Walls (with tappable Width column) ──
          const _SectionLabel('Walls',
              icon: Icons.crop_square_outlined,
              color: Color(0xFF2E7D32)),
          const SizedBox(height: 6),
          if (walls != null && walls.isNotEmpty)
            _buildWallsTable(context, walls)
          else
            const _PlaceholderNote(
                'No wall data found. Analyse a building plan to populate this section.'),
          const SizedBox(height: 16),

          // ── Door Schedule ──
          const _SectionLabel('Door Schedule',
              icon: Icons.door_front_door_outlined,
              color: Color(0xFF5D4037)),
          const SizedBox(height: 6),
          if (doors != null && doors.isNotEmpty)
            _MeasurementTable(
              color: const Color(0xFF5D4037),
              headers: const ['Door', 'Width', 'Height', 'Type', 'Qty'],
              rows: doors.entries.map((e) {
                final d = _map(e.value);
                return [
                  e.key,
                  _fmt(d?['width']),
                  _fmt(d?['height']),
                  _fmt(d?['type']),
                  _fmt(d?['quantity']),
                ];
              }).toList(),
            )
          else
            const _PlaceholderNote('No door schedule found.'),
          const SizedBox(height: 16),

          // ── Window & FW Schedule ──
          const _SectionLabel('Window & FW Schedule',
              icon: Icons.window_outlined,
              color: Color(0xFF00695C)),
          const SizedBox(height: 6),
          if (windows != null && windows.isNotEmpty)
            _MeasurementTable(
              color: const Color(0xFF00695C),
              headers: const ['Mark', 'Width', 'Height', 'Type', 'Qty'],
              rows: windows.entries.map((e) {
                final w = _map(e.value);
                return [
                  e.key,
                  _fmt(w?['width']),
                  _fmt(w?['height']),
                  _fmt(w?['type']),
                  _fmt(w?['quantity']),
                ];
              }).toList(),
            )
          else
            const _PlaceholderNote('No window / FW schedule found.'),
        ],
      ],
    );
  }

  // Walls table with tappable width cells
  Widget _buildWallsTable(BuildContext ctx, Map<String, dynamic> walls) {
    const color = Color(0xFF2E7D32);
    return ClipRRect(
      borderRadius: BorderRadius.circular(10),
      child: Table(
        border: TableBorder.all(color: color.withAlpha(40), width: 1),
        columnWidths: const {
          0: FlexColumnWidth(1.4),
          1: FlexColumnWidth(1.3),
          2: FlexColumnWidth(1.0),
          3: FlexColumnWidth(1.0),
        },
        children: [
          TableRow(
            decoration: BoxDecoration(color: color.withAlpha(30)),
            children: ['Wall', 'Width \u270E', 'Length', 'Height']
                .map((h) => _hCell(h, color))
                .toList(),
          ),
          ...walls.entries.toList().asMap().entries.map((entry) {
            final idx = entry.key;
            final e = entry.value;
            final w = e.value is Map<String, dynamic>
                ? e.value as Map<String, dynamic>
                : <String, dynamic>{};
            final widthVal = _wallWidth(e.key, w['width']);
            return TableRow(
              decoration: BoxDecoration(
                  color: idx.isEven ? Colors.white : color.withAlpha(8)),
              children: [
                _dCell(e.key, color),
                // Tappable width cell
                GestureDetector(
                  onTap: () => _pickBrickWidth(ctx, e.key, widthVal),
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 8, vertical: 7),
                    color: Colors.transparent,
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Flexible(
                          child: Text(
                            widthVal,
                            style: const TextStyle(
                              fontSize: 12,
                              color: Color(0xFF1565C0),
                              fontWeight: FontWeight.w600,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ),
                        const SizedBox(width: 3),
                        const Icon(Icons.edit_outlined,
                            size: 11, color: Color(0xFF1565C0)),
                      ],
                    ),
                  ),
                ),
                _dCell(_fmt(w['length']), color),
                _dCell(_fmt(w['height']), color),
              ],
            );
          }),
        ],
      ),
    );
  }

  Widget _hCell(String t, Color c) => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 7),
        child: Text(t,
            style: TextStyle(
                fontSize: 11, fontWeight: FontWeight.bold, color: c),
            textAlign: TextAlign.center),
      );

  Widget _dCell(String t, Color c) => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 7),
        child: Text(t.isEmpty ? '—' : t,
            style: const TextStyle(fontSize: 12, color: Colors.black87),
            textAlign: TextAlign.center),
      );
}

"""

# ─────────────────────────────────────────────────────────────────────────────
# NEW _SFContent  (StatefulWidget — column table with clickable width/length)
# ─────────────────────────────────────────────────────────────────────────────
NEW_SF = r"""//  Structural Frame Content

class _SFContent extends StatefulWidget {
  final Map<String, dynamic>? sfData;
  const _SFContent({this.sfData});

  @override
  State<_SFContent> createState() => _SFContentState();
}

class _SFContentState extends State<_SFContent> {
  // column key -> {width, length} overrides
  final Map<String, String> _widthOverrides = {};
  final Map<String, String> _lengthOverrides = {};

  // Standard square column sizes (width == length for each)
  static const _columnSizes = [
    {'label': '225 \u00d7 225 mm  (9\u2033 \u00d7 9\u2033 — default)', 'dim': '0.2250 m'},
    {'label': '300 \u00d7 300 mm  (12\u2033 \u00d7 12\u2033)', 'dim': '0.3000 m'},
    {'label': '375 \u00d7 375 mm  (15\u2033 \u00d7 15\u2033)', 'dim': '0.3750 m'},
    {'label': '450 \u00d7 450 mm  (18\u2033 \u00d7 18\u2033)', 'dim': '0.4500 m'},
    {'label': '600 \u00d7 600 mm  (24\u2033 \u00d7 24\u2033)', 'dim': '0.6000 m'},
  ];

  Map<String, dynamic>? _map(dynamic v) =>
      v is Map<String, dynamic> ? v : null;

  String _fmt(dynamic v) {
    if (v == null) return '';
    final s = v.toString().trim();
    return (s.isEmpty || s == 'null') ? '' : s;
  }

  String _colDim(Map<String, String> overrides, String key, dynamic raw,
      String defaultVal) {
    if (overrides.containsKey(key)) return overrides[key]!;
    final v = _fmt(raw);
    return v.isEmpty ? defaultVal : v;
  }

  void _pickColumnSize(
      BuildContext ctx, String colKey, String whichDim, String current) {
    showModalBottomSheet(
      context: ctx,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (_) => _SizePickerSheet(
        title: 'Select Column $whichDim  ($colKey)',
        items: _columnSizes.map((s) => s['label']!).toList(),
        currentValue: current,
        onSelect: (idx) {
          final val = _columnSizes[idx]['dim']!;
          setState(() {
            if (whichDim == 'Width') {
              _widthOverrides[colKey] = val;
            } else {
              _lengthOverrides[colKey] = val;
            }
          });
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (widget.sfData == null) {
      return const _PlaceholderNote(
          'No structural frame data found. Analyse a building plan first.');
    }

    final raw = _map(widget.sfData!['data']) ?? widget.sfData!;
    final output = _map(raw['output']);
    final groundFloor = _map(raw['groundFloor']);
    final columns = _map(groundFloor?['columns']);
    final totalColumns =
        output?['totalColumns']?.toString() ?? columns?.length.toString() ?? '—';
    final units = _fmt(output?['units']);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Summary
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: const Color(0xFF1565C0).withAlpha(12),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: const Color(0xFF1565C0).withAlpha(40)),
          ),
          child: Row(children: [
            const Icon(Icons.account_tree_outlined,
                size: 16, color: Color(0xFF1565C0)),
            const SizedBox(width: 8),
            Text(
              'Total Columns: $totalColumns',
              style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF1565C0)),
            ),
            if (units.isNotEmpty) ...[
              const Spacer(),
              Text('Units: $units',
                  style: TextStyle(fontSize: 12, color: Colors.grey.shade600)),
            ],
          ]),
        ),
        const SizedBox(height: 12),
        if (columns != null && columns.isNotEmpty)
          _buildColumnsTable(context, columns)
        else
          const _PlaceholderNote('No column data available.'),
      ],
    );
  }

  Widget _buildColumnsTable(
      BuildContext ctx, Map<String, dynamic> columns) {
    const color = Color(0xFF1565C0);
    const defaultDim = '0.2250 m';
    return ClipRRect(
      borderRadius: BorderRadius.circular(10),
      child: Table(
        border: TableBorder.all(color: color.withAlpha(40), width: 1),
        columnWidths: const {
          0: FlexColumnWidth(1.4),
          1: FlexColumnWidth(1.3),
          2: FlexColumnWidth(1.3),
          3: FlexColumnWidth(1.0),
        },
        children: [
          TableRow(
            decoration: BoxDecoration(color: color.withAlpha(30)),
            children: ['Column', 'Width \u270E', 'Length \u270E', 'Height']
                .map((h) => _hCell(h, color))
                .toList(),
          ),
          ...columns.entries.toList().asMap().entries.map((entry) {
            final idx = entry.key;
            final e = entry.value;
            final c = e.value is Map<String, dynamic>
                ? e.value as Map<String, dynamic>
                : <String, dynamic>{};
            final wVal = _colDim(_widthOverrides, e.key, c['width'], defaultDim);
            final lVal = _colDim(_lengthOverrides, e.key, c['length'], defaultDim);
            return TableRow(
              decoration: BoxDecoration(
                  color: idx.isEven ? Colors.white : color.withAlpha(8)),
              children: [
                _dCell(e.key, color),
                // Tappable width
                _tappableCell(
                    wVal, () => _pickColumnSize(ctx, e.key, 'Width', wVal),
                    color),
                // Tappable length
                _tappableCell(
                    lVal, () => _pickColumnSize(ctx, e.key, 'Length', lVal),
                    color),
                _dCell(_fmt(c['height']), color),
              ],
            );
          }),
        ],
      ),
    );
  }

  Widget _tappableCell(String value, VoidCallback onTap, Color color) =>
      GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 7),
          color: Colors.transparent,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Flexible(
                child: Text(
                  value,
                  style: const TextStyle(
                    fontSize: 12,
                    color: Color(0xFF1565C0),
                    fontWeight: FontWeight.w600,
                  ),
                  textAlign: TextAlign.center,
                ),
              ),
              const SizedBox(width: 3),
              const Icon(Icons.edit_outlined,
                  size: 11, color: Color(0xFF1565C0)),
            ],
          ),
        ),
      );

  Widget _hCell(String t, Color c) => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 7),
        child: Text(t,
            style: TextStyle(
                fontSize: 11, fontWeight: FontWeight.bold, color: c),
            textAlign: TextAlign.center),
      );

  Widget _dCell(String t, Color c) => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 7),
        child: Text(t.isEmpty ? '—' : t,
            style: const TextStyle(fontSize: 12, color: Colors.black87),
            textAlign: TextAlign.center),
      );
}

"""

# ─────────────────────────────────────────────────────────────────────────────
# _SectionLabel  and  _SizePickerSheet  — new helper widgets
# ─────────────────────────────────────────────────────────────────────────────
NEW_HELPERS = r"""//  Section label helper

class _SectionLabel extends StatelessWidget {
  final String title;
  final IconData icon;
  final Color color;
  const _SectionLabel(this.title, {required this.icon, required this.color});

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      Icon(icon, size: 14, color: color),
      const SizedBox(width: 6),
      Text(
        title,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w700,
          color: color,
          letterSpacing: 0.3,
        ),
      ),
    ]);
  }
}

//  Size Picker Bottom-Sheet

class _SizePickerSheet extends StatelessWidget {
  final String title;
  final List<String> items;
  final String currentValue;
  final void Function(int index) onSelect;
  const _SizePickerSheet({
    required this.title,
    required this.items,
    required this.currentValue,
    required this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.only(top: 16, bottom: 8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: Text(
                title,
                style: const TextStyle(
                    fontSize: 14, fontWeight: FontWeight.bold),
              ),
            ),
            const Divider(height: 8),
            ...items.asMap().entries.map((e) {
              final isSelected = e.value.contains(currentValue) ||
                  currentValue.contains(e.value.split(' ').first);
              return ListTile(
                dense: true,
                leading: Icon(
                  isSelected
                      ? Icons.radio_button_checked
                      : Icons.radio_button_unchecked,
                  size: 18,
                  color: isSelected
                      ? AppColors.primary
                      : Colors.grey.shade400,
                ),
                title: Text(e.value,
                    style: TextStyle(
                        fontSize: 13,
                        fontWeight: isSelected
                            ? FontWeight.w600
                            : FontWeight.normal)),
                onTap: () {
                  onSelect(e.key);
                  Navigator.pop(context);
                },
              );
            }),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }
}

"""

# ──────────────────────────────────────────────────────────────────────────────
# Now do the replacements
# ──────────────────────────────────────────────────────────────────────────────

MEAS_TABLE_SECTION = '\n\n// \u2500\u2500\u2500 Measurement Table'

# 1. Replace old _WallingContent block (up to _MeasurementTable comment)
walling_start = content.find('//  Walling Content ')
meas_table_start = content.find(MEAS_TABLE_SECTION)
assert walling_start != -1 and meas_table_start != -1
old_walling_block = content[walling_start:meas_table_start]
content = content.replace(old_walling_block, NEW_WALLING.rstrip(), 1)
print(f'[1] Replaced WallingContent ({len(old_walling_block)} chars -> {len(NEW_WALLING)} chars)')

# 2. Replace old _SFContent block (between _MeasurementTable section and _FinishingContent comment)
sf_start = content.find('//  Structural Frame Content')
finishing_content_start = content.find('//  Finishing Content ')
assert sf_start != -1 and finishing_content_start != -1
old_sf_block = content[sf_start:finishing_content_start]
content = content.replace(old_sf_block, NEW_SF.rstrip(), 1)
print(f'[2] Replaced SFContent ({len(old_sf_block)} chars -> {len(NEW_SF)} chars)')

# 3. Remove _FinishingContent class entirely (from finishing comment to //  Sub-widgets)
finishing_start = content.find('//  Finishing Content ')
subwidgets_start = content.find('//  Sub-widgets')
assert finishing_start != -1 and subwidgets_start != -1
old_finishing = content[finishing_start:subwidgets_start]
content = content.replace(old_finishing, '', 1)
print(f'[3] Removed FinishingContent ({len(old_finishing)} chars)')

# 4. Insert _SectionLabel and _SizePickerSheet BEFORE //  Sub-widgets
subwidgets_pos = content.find('//  Sub-widgets')
content = content[:subwidgets_pos] + NEW_HELPERS + content[subwidgets_pos:]
print(f'[4] Inserted _SectionLabel + _SizePickerSheet helpers ({len(NEW_HELPERS)} chars)')

# Write back
with open(TAB_PATH, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'\nDone! File written: {len(content)} chars')
