import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../providers/mongo_project_provider.dart';
import '../../../services/mongo_api_service.dart';

// ─── Entry point ─────────────────────────────────────────────────────────────

class OverviewTab extends StatefulWidget {
  /// Called when user taps Materials (tabIndex=1) or BOQ (tabIndex=3).
  /// For Materials, [roomLabel] and [roomData] carry the selected room context.
  final void Function(int tabIndex,
      {String? roomLabel, Map<String, dynamic>? roomData})? onNavigateToTab;
  const OverviewTab({super.key, this.onNavigateToTab});

  @override
  State<OverviewTab> createState() => _OverviewTabState();
}

class _OverviewTabState extends State<OverviewTab> {
  Map<String, dynamic>? _structure;
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _fetchStructure());
  }

  Future<void> _fetchStructure() async {
    final pid =
        Provider.of<ProjectProvider>(context, listen: false).currentProject?.projectId;
    if (pid == null || pid.isEmpty) return;
    setState(() { _loading = true; _error = null; });
    try {
      final api = MongoApiService();
      await api.loadToken();
      final result = await api.getBuildingStructure(pid);
      setState(() => _structure = result.isEmpty ? null : result);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final pp = context.watch<ProjectProvider>();
    final p = pp.currentProject;
    if (p == null) return const Center(child: Text('No project selected'));

    return RefreshIndicator(
      onRefresh: _fetchStructure,
      child: ListView(
        padding: const EdgeInsets.all(14),
        children: [
          // ── Building Structure ──────────────────────────────────────────
          _SectionHeader('Building Structure', Icons.foundation),
          const SizedBox(height: 10),

          if (_loading)
            const Center(
                child: Padding(
                    padding: EdgeInsets.all(32),
                    child: CircularProgressIndicator()))
          else if (_error != null)
            _ErrorCard(_error!, onRetry: _fetchStructure)
          else if (_structure == null)
            _NoStructureCard(projectId: p.projectId, onUploaded: _fetchStructure)
          else
            _BuildingStructureView(
              data: _structure!,
              onNavigateToTab: widget.onNavigateToTab,
            ),

          const SizedBox(height: 24),
        ],
      ),
    );
  }
}

// ─── Building Structure renderer ─────────────────────────────────────────────

class _BuildingStructureView extends StatelessWidget {
  final Map<String, dynamic> data;
  final void Function(int, {String? roomLabel, Map<String, dynamic>? roomData})? onNavigateToTab;
  const _BuildingStructureView({required this.data, this.onNavigateToTab});

  Map<String, dynamic>? _map(dynamic v) =>
      v is Map<String, dynamic> ? v : null;

  List<dynamic> _list(dynamic v) => v is List ? v : [];

  String _fmt(dynamic v, {String units = ''}) {
    if (v == null) return '—';
    final s = v.toString().trim();
    if (s.isEmpty || s == 'null') return '—';
    return units.isNotEmpty ? '$s $units' : s;
  }

  @override
  Widget build(BuildContext context) {
    // The backend wraps the Gemini JSON inside a `data` key
    final raw = _map(data['data']) ?? data;

    final output  = _map(raw['output']);
    final levels  = _map(raw['levels']);
    final floors  = _map(raw['floors']);
    final catalog = _map(raw['openingsCatalog']);
    final ratios  = _map(raw['ratios']);
    final warnings = _list(raw['extractionWarnings']);
    final units   = output?['units']?.toString() ?? '';

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      // ── Output info ──────────────────────────────────────────────────
      if (output != null) ...[
        _SectionCard(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          _CardHeader(Icons.info_outline, 'Plan Info'),
          const SizedBox(height: 8),
          _KVTable([
            ['Units', _fmt(output['units'])],
            ['Scale', _fmt(output['scaleText'])],
            ['Floor Area (reported)', _fmt(output['floorAreaReported'])],
          ]),
          if (_list(output['notes']).isNotEmpty)
            _NoteChips(_list(output['notes'])),
        ])),
        const SizedBox(height: 10),
      ],

      // ── Ratios ───────────────────────────────────────────────────────
      if (ratios != null &&
          (ratios['concreteMix'] != null ||
           ratios['mortarMix']   != null ||
           ratios['plasterMix']  != null)) ...[
        _SectionCard(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          _CardHeader(Icons.science_outlined, 'Mix Ratios'),
          const SizedBox(height: 8),
          _KVTable([
            ['Concrete Mix', _fmt(ratios['concreteMix'])],
            ['Mortar Mix',   _fmt(ratios['mortarMix'])],
            ['Plaster Mix',  _fmt(ratios['plasterMix'])],
          ]),
        ])),
        const SizedBox(height: 10),
      ],

      // ── Levels ───────────────────────────────────────────────────────
      if (levels != null) ...[
        _SectionCard(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          _CardHeader(Icons.layers_outlined, 'Level Measurements'),
          const SizedBox(height: 10),
          if (_map(levels['groundFloor']) != null)
            _LevelTable('Ground Floor', _map(levels['groundFloor'])!, units),
          if (_map(levels['upperFloor']) != null) ...[
            const SizedBox(height: 10),
            _LevelTable('Upper Floor', _map(levels['upperFloor'])!, units),
          ],
        ])),
        const SizedBox(height: 10),
      ],

      // ── Openings catalog ─────────────────────────────────────────────
      if (catalog != null) ...[
        _SectionCard(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          _CardHeader(Icons.door_front_door_outlined, 'Openings Catalogue'),
          const SizedBox(height: 8),
          if (_list(catalog['doors']).isNotEmpty)
            _OpeningCatalogTable('Doors', _list(catalog['doors']), units),
          if (_list(catalog['windows']).isNotEmpty) ...[
            const SizedBox(height: 8),
            _OpeningCatalogTable('Windows', _list(catalog['windows']), units),
          ],
          if (_list(catalog['frenchWindows']).isNotEmpty) ...[
            const SizedBox(height: 8),
            _OpeningCatalogTable('French Windows', _list(catalog['frenchWindows']), units),
          ],
          if (_list(catalog['fanlights']).isNotEmpty) ...[
            const SizedBox(height: 8),
            _OpeningCatalogTable('Fanlights', _list(catalog['fanlights']), units),
          ],
        ])),
        const SizedBox(height: 10),
      ],

      // ── Floor spaces ─────────────────────────────────────────────────
      if (floors != null) ...[
        _FloorSpaces(
          floorKey: 'groundFloor',
          label: 'Ground Floor Spaces',
          floors: floors,
          units: units,
          onNavigateToTab: onNavigateToTab,
        ),
        if (_map(floors['upperFloor'])?['enabled'] == true ||
            (_map(_map(floors['upperFloor'])?['spaces'])?.isNotEmpty ?? false)) ...[
          const SizedBox(height: 10),
          _FloorSpaces(
            floorKey: 'upperFloor',
            label: 'Upper Floor Spaces',
            floors: floors,
            units: units,
            onNavigateToTab: onNavigateToTab,
          ),
        ],
      ],

      // ── Extraction warnings ──────────────────────────────────────────
      if (warnings.isNotEmpty) ...[
        const SizedBox(height: 10),
        _WarningsCard(warnings),
      ],
    ]);
  }
}

// ─── Floor spaces section ─────────────────────────────────────────────────────

class _FloorSpaces extends StatefulWidget {
  final String floorKey;
  final String label;
  final Map<String, dynamic> floors;
  final String units;
  final void Function(int, {String? roomLabel, Map<String, dynamic>? roomData})? onNavigateToTab;

  const _FloorSpaces({
    required this.floorKey,
    required this.label,
    required this.floors,
    required this.units,
    this.onNavigateToTab,
  });

  @override
  State<_FloorSpaces> createState() => _FloorSpacesState();
}

class _FloorSpacesState extends State<_FloorSpaces> {
  String? _selectedKey;

  Map<String, dynamic>? _map(dynamic v) =>
      v is Map<String, dynamic> ? v : null;

  String _fmt(dynamic v) {
    if (v == null) return '—';
    final s = v.toString().trim();
    return (s.isEmpty || s == 'null') ? '—' : s;
  }

  @override
  Widget build(BuildContext context) {
    final floorData = _map(widget.floors[widget.floorKey]);
    final spacesRaw = _map(floorData?['spaces']);
    if (spacesRaw == null || spacesRaw.isEmpty) return const SizedBox.shrink();

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _SectionHeader(widget.label, Icons.home_outlined),
      const SizedBox(height: 8),
      _SectionCard(
        child: Column(
          children: spacesRaw.entries.map((entry) {
            final room    = _map(entry.value);
            final lbl     = _fmt(room?['labelText'] ?? entry.key);
            final area    = room?['floor'] is Map ? room!['floor']['area'] : null;
            final areaStr = area != null && area.toString() != 'null'
                ? 'Area: $area ${widget.units}²'
                : '';
            final isLast     = entry.key == spacesRaw.keys.last;
            final isSelected = _selectedKey == entry.key;

            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 4),
                  child: Row(children: [
                    Container(
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1565C0).withAlpha(18),
                        borderRadius: BorderRadius.circular(7),
                      ),
                      child: const Icon(Icons.meeting_room_outlined,
                          size: 16, color: Color(0xFF1565C0)),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(lbl,
                              style: const TextStyle(
                                  fontWeight: FontWeight.w600, fontSize: 13)),
                          if (areaStr.isNotEmpty)
                            Text(areaStr,
                                style: TextStyle(
                                    fontSize: 11, color: Colors.grey[600])),
                        ],
                      ),
                    ),
                    TextButton(
                      onPressed: () {
                        if (room != null) {
                          setState(() {
                            _selectedKey = isSelected ? null : entry.key;
                          });
                        }
                      },
                      style: TextButton.styleFrom(
                        foregroundColor: Colors.white,
                        backgroundColor: isSelected
                            ? Colors.grey[600]
                            : const Color(0xFF1565C0),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 14, vertical: 6),
                        minimumSize: Size.zero,
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8)),
                      ),
                      child: Text(isSelected ? 'Close' : 'View',
                          style: const TextStyle(
                              fontSize: 12, fontWeight: FontWeight.w600)),
                    ),
                  ]),
                ),
                // ── Inline room detail panel ──────────────────────────
                if (isSelected && room != null) ...[  
                  _RoomDetailPanel(
                    label:    lbl,
                    roomData: room,
                    units:    widget.units,
                    onClose:  () => setState(() => _selectedKey = null),
                    onMaterials: () => widget.onNavigateToTab?.call(
                        1, roomLabel: lbl, roomData: room),
                    onBoq:       () => widget.onNavigateToTab?.call(3),
                  ),
                  const SizedBox(height: 8),
                ],
                if (!isLast && !isSelected) const Divider(height: 1),
              ],
            );
          }).toList(),
        ),
      ),
    ]);
  }
}

// ─── Room detail panel (shown at top when View is tapped) ─────────────────────

class _RoomDetailPanel extends StatelessWidget {
  final String label;
  final Map<String, dynamic> roomData;
  final String units;
  final VoidCallback onClose;
  final VoidCallback? onMaterials;
  final VoidCallback? onBoq;

  const _RoomDetailPanel({
    required this.label,
    required this.roomData,
    required this.units,
    required this.onClose,
    this.onMaterials,
    this.onBoq,
  });

  Map<String, dynamic>? _map(dynamic v) =>
      v is Map<String, dynamic> ? v : null;

  String _fmt(dynamic v) {
    if (v == null) return '—';
    final s = v.toString().trim();
    return (s.isEmpty || s == 'null') ? '—' : s;
  }

  @override
  Widget build(BuildContext context) {
    final floor    = _map(roomData['floor']);
    final walls    = _map(roomData['walls']);
    final openings = _map(roomData['openings']);
    final u        = units;

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF1565C0).withAlpha(60), width: 1.5),
        boxShadow: [
          BoxShadow(
              color: const Color(0xFF1565C0).withAlpha(18),
              blurRadius: 12,
              offset: const Offset(0, 3)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Header ───────────────────────────────────────────────────
          Container(
            padding: const EdgeInsets.fromLTRB(14, 12, 10, 12),
            decoration: const BoxDecoration(
              color: Color(0xFF1565C0),
              borderRadius: BorderRadius.vertical(top: Radius.circular(13)),
            ),
            child: Row(children: [
              const Icon(Icons.meeting_room_outlined, size: 18, color: Colors.white),
              const SizedBox(width: 8),
              Expanded(
                child: Text(label,
                    style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 15)),
              ),
              GestureDetector(
                onTap: onClose,
                child: const Icon(Icons.close, color: Colors.white70, size: 20),
              ),
            ]),
          ),

          // ── Body ─────────────────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Floor dimensions
                if (floor != null) ...[
                  _SubHeader('Floor Dimensions'),
                  _KVTable([
                    ['Length', _fmt(floor['length']) == '—' ? '—' : '${_fmt(floor['length'])} $u'],
                    ['Width',  _fmt(floor['width'])  == '—' ? '—' : '${_fmt(floor['width'])} $u'],
                    ['Area',   _fmt(floor['area'])   == '—' ? '—' : '${_fmt(floor['area'])} ${u}²'],
                  ]),
                  const SizedBox(height: 12),
                ],
                // Walls
                if (walls != null && walls.isNotEmpty) ...[
                  _SubHeader('Walls'),
                  _WallsTable(walls, u),
                  const SizedBox(height: 12),
                ],
                // Openings
                if (openings != null) ...[
                  _OpeningsSection(openings, u),
                  const SizedBox(height: 12),
                ],
                // ── Action buttons ───────────────────────────────────
                const Divider(height: 1),
                const SizedBox(height: 12),
                Row(children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: onMaterials,
                      icon: const Icon(Icons.inventory_2_outlined, size: 16),
                      label: const Text('Materials',
                          style: TextStyle(fontWeight: FontWeight.w600)),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.green.shade700,
                        side: BorderSide(color: Colors.green.shade400),
                        padding: const EdgeInsets.symmetric(vertical: 10),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10)),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: onBoq,
                      icon: const Icon(Icons.format_list_numbered, size: 16),
                      label: const Text('BOQ',
                          style: TextStyle(fontWeight: FontWeight.w600)),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.orange.shade700,
                        side: BorderSide(color: Colors.orange.shade400),
                        padding: const EdgeInsets.symmetric(vertical: 10),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10)),
                      ),
                    ),
                  ),
                ]),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Walls compact table ──────────────────────────────────────────────────────

class _WallsTable extends StatelessWidget {
  final Map<String, dynamic> walls;
  final String units;
  const _WallsTable(this.walls, this.units);

  String _fmt(dynamic v) {
    if (v == null) return '—';
    final s = v.toString().trim();
    return (s.isEmpty || s == 'null') ? '—' : s;
  }

  @override
  Widget build(BuildContext context) {
    final rows = walls.entries.toList();
    return Table(
      columnWidths: const {
        0: IntrinsicColumnWidth(),
        1: FlexColumnWidth(),
        2: FlexColumnWidth(),
        3: FlexColumnWidth(),
      },
      border: TableBorder.all(
          color: Colors.grey.shade200, borderRadius: BorderRadius.circular(8)),
      children: [
        TableRow(
          decoration: BoxDecoration(color: Colors.grey.shade100),
          children: [
            _TH('Wall'),
            _TH('Length ($units)'),
            _TH('Thick ($units)'),
            _TH('Adjacent To'),
          ],
        ),
        ...rows.map((e) {
          final w = e.value is Map<String, dynamic>
              ? e.value as Map<String, dynamic>
              : <String, dynamic>{};
          return TableRow(children: [
            _TD(e.key, bold: true),
            _TD(_fmt(w['length'])),
            _TD(_fmt(w['thickness'])),
            _TD(_fmt(w['adjacentTo'])),
          ]);
        }),
      ],
    );
  }
}

// ─── Openings for a room ──────────────────────────────────────────────────────

class _OpeningsSection extends StatelessWidget {
  final Map<String, dynamic> openings;
  final String units;
  const _OpeningsSection(this.openings, this.units);

  List<dynamic> _list(dynamic v) => v is List ? v : [];

  @override
  Widget build(BuildContext context) {
    final doors   = _list(openings['doors']);
    final windows = _list(openings['windows']);
    final french  = _list(openings['frenchWindows']);
    final fans    = _list(openings['fanlights']);
    if (doors.isEmpty && windows.isEmpty && french.isEmpty && fans.isEmpty) {
      return const SizedBox.shrink();
    }
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _SubHeader('Openings'),
      if (doors.isNotEmpty)
        _OpeningRows('Doors',          doors,   Icons.door_front_door_outlined, Colors.brown,  units),
      if (windows.isNotEmpty)
        _OpeningRows('Windows',        windows, Icons.window_outlined,          Colors.blue,   units),
      if (french.isNotEmpty)
        _OpeningRows('French Windows', french,  Icons.balcony_outlined,         Colors.teal,   units),
      if (fans.isNotEmpty)
        _OpeningRows('Fanlights',      fans,    Icons.light_outlined,           Colors.amber,  units),
    ]);
  }
}

class _OpeningRows extends StatelessWidget {
  final String label;
  final List<dynamic> items;
  final IconData icon;
  final Color color;
  final String units;
  const _OpeningRows(this.label, this.items, this.icon, this.color, this.units);

  String _fmt(dynamic v) {
    if (v == null) return '—';
    final s = v.toString().trim();
    return (s.isEmpty || s == 'null') ? '—' : s;
  }

  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 4),
          Text(label,
              style: TextStyle(
                  fontSize: 12, fontWeight: FontWeight.w600, color: color)),
        ]),
      ),
      Table(
        columnWidths: const {
          0: IntrinsicColumnWidth(),
          1: FlexColumnWidth(),
          2: FlexColumnWidth(),
          3: FlexColumnWidth(),
        },
        border: TableBorder.all(
            color: Colors.grey.shade200, borderRadius: BorderRadius.circular(6)),
        children: [
          TableRow(
            decoration: BoxDecoration(color: Colors.grey.shade100),
            children: [
              _TH('ID'),
              _TH('Code'),
              _TH('W ($units)'),
              _TH('H ($units)'),
            ],
          ),
          ...items.map((item) {
            final m = item is Map<String, dynamic> ? item : <String, dynamic>{};
            return TableRow(children: [
              _TD(_fmt(m['openingId']), bold: true),
              _TD(_fmt(m['typeCode'])),
              _TD(_fmt(m['width'])),
              _TD(_fmt(m['height'])),
            ]);
          }),
        ],
      ),
      const SizedBox(height: 6),
    ]);
  }
}

// ─── Level measurements table ─────────────────────────────────────────────────

class _LevelTable extends StatelessWidget {
  final String label;
  final Map<String, dynamic> level;
  final String units;
  const _LevelTable(this.label, this.level, this.units);

  String _fmt(dynamic v) {
    if (v == null) return '—';
    final s = v.toString().trim();
    return (s.isEmpty || s == 'null') ? '—' : s;
  }

  @override
  Widget build(BuildContext context) {
    final u = units.isNotEmpty ? ' ($units)' : '';
    final rows = <List<String>>[
      if (level['plinthHeight'] != null)
        ['Plinth Height$u', _fmt(level['plinthHeight'])],
      ['Clear Height$u',    _fmt(level['clearHeight'])],
      ['Slab Thickness$u',  _fmt(level['slabThickness'])],
      ['Beam Depth$u',      _fmt(level['beamDepth'])],
      ['Beam Width$u',      _fmt(level['beamWidth'])],
      if (level['lintelLevel'] != null)
        ['Lintel Level$u',  _fmt(level['lintelLevel'])],
      if (level['defaultWindowSillHeight'] != null)
        ['Window Sill$u',   _fmt(level['defaultWindowSillHeight'])],
      if (level['defaultWindowHeadHeight'] != null)
        ['Window Head$u',   _fmt(level['defaultWindowHeadHeight'])],
    ];

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(label,
          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
      const SizedBox(height: 6),
      _KVTable(rows),
    ]);
  }
}

// ─── Catalogue table ──────────────────────────────────────────────────────────

class _OpeningCatalogTable extends StatelessWidget {
  final String label;
  final List<dynamic> items;
  final String units;
  const _OpeningCatalogTable(this.label, this.items, this.units);

  String _fmt(dynamic v) {
    if (v == null) return '—';
    final s = v.toString().trim();
    return (s.isEmpty || s == 'null') ? '—' : s;
  }

  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(label,
          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
      const SizedBox(height: 4),
      Table(
        columnWidths: const {
          0: IntrinsicColumnWidth(),
          1: FlexColumnWidth(),
          2: FlexColumnWidth(),
          3: FlexColumnWidth(),
        },
        border: TableBorder.all(
            color: Colors.grey.shade200, borderRadius: BorderRadius.circular(8)),
        children: [
          TableRow(
            decoration: BoxDecoration(color: Colors.grey.shade100),
            children: [
              _TH('Code'),
              _TH('Type'),
              _TH('W (${units.isNotEmpty ? units : "—"})'),
              _TH('H (${units.isNotEmpty ? units : "—"})'),
            ],
          ),
          ...items.map((item) {
            final m = item is Map<String, dynamic> ? item : <String, dynamic>{};
            return TableRow(children: [
              _TD(_fmt(m['typeCode'] ?? m['code']), bold: true),
              _TD(_fmt(m['type'] ?? m['description'] ?? '—')),
              _TD(_fmt(m['width'])),
              _TD(_fmt(m['height'])),
            ]);
          }),
        ],
      ),
    ]);
  }
}

// ─── Warnings card ────────────────────────────────────────────────────────────

class _WarningsCard extends StatefulWidget {
  final List<dynamic> warnings;
  const _WarningsCard(this.warnings);

  @override
  State<_WarningsCard> createState() => _WarningsCardState();
}

class _WarningsCardState extends State<_WarningsCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.orange.shade50,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => setState(() => _expanded = !_expanded),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Icon(Icons.warning_amber_rounded,
                  color: Colors.orange.shade700, size: 18),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  'Extraction Warnings (${widget.warnings.length})',
                  style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.orange.shade800,
                      fontSize: 13),
                ),
              ),
              Icon(_expanded
                  ? Icons.keyboard_arrow_up
                  : Icons.keyboard_arrow_down,
                  color: Colors.orange.shade700),
            ]),
            if (_expanded) ...[
              const SizedBox(height: 8),
              ...widget.warnings.map((w) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 2),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('• ',
                            style: TextStyle(color: Colors.orange.shade700)),
                        Expanded(
                          child: Text(w.toString(),
                              style: TextStyle(
                                  fontSize: 12, color: Colors.orange.shade900)),
                        ),
                      ],
                    ),
                  )),
            ],
          ]),
        ),
      ),
    );
  }
}

// ─── No structure card ────────────────────────────────────────────────────────

class _NoStructureCard extends StatelessWidget {
  final String projectId;
  final VoidCallback onUploaded;
  const _NoStructureCard({required this.projectId, required this.onUploaded});

  @override
  Widget build(BuildContext context) {
    return _SectionCard(
      child: Column(children: [
        const Icon(Icons.architecture_outlined, size: 48, color: Color(0xFF1565C0)),
        const SizedBox(height: 10),
        const Text('No Building Structure Data',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
        const SizedBox(height: 6),
        const Text(
          'Upload building plan images to let Gemini extract a full '
          'room-by-room structural breakdown.',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 12, color: Colors.grey),
        ),
      ]),
    );
  }
}

// ─── Error card ───────────────────────────────────────────────────────────────

class _ErrorCard extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _ErrorCard(this.message, {required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return _SectionCard(
      child: Column(children: [
        const Icon(Icons.error_outline, size: 36, color: Colors.red),
        const SizedBox(height: 8),
        Text(message,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 12, color: Colors.red)),
        const SizedBox(height: 10),
        TextButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh),
            label: const Text('Retry')),
      ]),
    );
  }
}

// ─── Shared small widgets ─────────────────────────────────────────────────────

class _SectionHeader extends StatelessWidget {
  final String title;
  final IconData icon;
  const _SectionHeader(this.title, this.icon);

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      Icon(icon, size: 18, color: const Color(0xFF1565C0)),
      const SizedBox(width: 6),
      Text(title,
          style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.bold,
              color: Color(0xFF1565C0))),
    ]);
  }
}

class _CardHeader extends StatelessWidget {
  final IconData icon;
  final String title;
  const _CardHeader(this.icon, this.title);

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      Icon(icon, size: 16, color: const Color(0xFF1565C0)),
      const SizedBox(width: 6),
      Text(title,
          style: const TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 14,
              color: Color(0xFF1565C0))),
    ]);
  }
}

class _SubHeader extends StatelessWidget {
  final String title;
  const _SubHeader(this.title);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Text(title,
          style: const TextStyle(
              fontWeight: FontWeight.w600, fontSize: 12, color: Colors.black87)),
    );
  }
}

class _KVTable extends StatelessWidget {
  final List<List<String>> rows;
  const _KVTable(this.rows);

  @override
  Widget build(BuildContext context) {
    return Table(
      columnWidths: const {
        0: IntrinsicColumnWidth(),
        1: FlexColumnWidth(),
      },
      children: rows.map((row) {
        return TableRow(children: [
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 4),
            child: Text(row[0],
                style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[700],
                    fontWeight: FontWeight.w500)),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
            child: Text(row.length > 1 ? row[1] : '—',
                style: const TextStyle(
                    fontSize: 12, fontWeight: FontWeight.w600)),
          ),
        ]);
      }).toList(),
    );
  }
}

class _TH extends StatelessWidget {
  final String text;
  const _TH(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 6),
      child: Text(text,
          style: const TextStyle(
              fontSize: 11, fontWeight: FontWeight.bold, color: Colors.black87)),
    );
  }
}

class _TD extends StatelessWidget {
  final String text;
  final bool bold;
  const _TD(this.text, {this.bold = false});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 5),
      child: Text(text,
          style: TextStyle(
              fontSize: 11,
              fontWeight: bold ? FontWeight.w600 : FontWeight.normal)),
    );
  }
}

class _NoteChips extends StatelessWidget {
  final List<dynamic> notes;
  const _NoteChips(this.notes);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 6),
      child: Wrap(
        spacing: 6,
        runSpacing: 4,
        children: notes
            .map((n) => Chip(
                  label: Text(n.toString(),
                      style: const TextStyle(fontSize: 10)),
                  padding: EdgeInsets.zero,
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  backgroundColor: Colors.blue.shade50,
                ))
            .toList(),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  const _InfoRow(this.icon, this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(children: [
        Icon(icon, size: 15, color: Colors.grey[500]),
        const SizedBox(width: 6),
        Text('$label: ',
            style: TextStyle(color: Colors.grey[600], fontSize: 12)),
        Expanded(
          child: Text(value,
              style: const TextStyle(
                  fontWeight: FontWeight.w500, fontSize: 12)),
        ),
      ]),
    );
  }
}

class _SectionCard extends StatelessWidget {
  final Widget child;
  const _SectionCard({required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withAlpha(13),
              blurRadius: 8,
              offset: const Offset(0, 2))
        ],
      ),
      child: child,
    );
  }
}
