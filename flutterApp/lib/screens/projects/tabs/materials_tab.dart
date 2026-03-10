import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';
import '../../../providers/mongo_project_provider.dart';
import '../../../models/project/material_model.dart';
import '../../../services/mongo_api_service.dart';
import '../material_library_screen.dart';

// ─── Image asset maps ─────────────────────────────────────────────────────────

/// Returns the asset path for a material name (loose match).
String? _matImagePath(String name) {
  final n = name.toLowerCase();
  if (n.contains('cement block') || n.contains('concrete block') || n.contains('hollow')) return 'AppImages/materials/cementBlock.png';
  if (n.contains('cement'))       return 'AppImages/materials/cement.png';
  if (n.contains('sand'))         return 'AppImages/materials/sand.png';
  if (n.contains('aggregate'))    return 'AppImages/materials/aggregates.png';
  if (n.contains('steel') || n.contains('rebar') || n.contains('lintel')) return 'AppImages/materials/steels.png';
  if (n.contains('binding wire')) return 'AppImages/materials/bindingWire.png';
  if (n.contains('nail'))         return 'AppImages/materials/nails.png';
  if (n.contains('tile') || n.contains('skirting')) return 'AppImages/materials/tile.png';
  if (n.contains('paint') || n.contains('ceiling paint') || n.contains('exterior paint')) return 'AppImages/materials/wallPaint.png';
  if (n.contains('primer') || n.contains('filler')) return 'AppImages/materials/fillerPaints.png';
  if (n.contains('putty') || n.contains('puty'))    return 'AppImages/materials/puty.png';
  if (n.contains('brick'))        return 'AppImages/materials/brick.png';
  if (n.contains('block'))        return 'AppImages/materials/cementBlock.png';
  return null;
}

/// Returns the asset path for a brand name (loose match).
String? _brandLogoPath(String brand) {
  final b = brand.toLowerCase();
  if (b.contains('causeway'))             return 'AppImages/brands/causewayPaints.png';
  if (b.contains('dulux'))                return 'AppImages/brands/duluxPaints.png';
  if (b.contains('lanwa'))                return 'AppImages/brands/lanwaCement.png';
  if (b.contains('robbialac') || b.contains('robialac')) return 'AppImages/brands/robbialacPaints.png';
  if (b.contains('sanstha'))              return 'AppImages/brands/sansthaCement.png';
  if (b.contains('taian') || b.contains('taiian'))       return 'AppImages/brands/taianSteels.png';
  return null;
}

// ─────────────────────────────────────────────────────────────────────────────
// Material blueprint definitions  (process → items)
// ─────────────────────────────────────────────────────────────────────────────

const List<_ProcessSection> _kBlueprint = [
  _ProcessSection(
    icon: Icons.foundation,
    label: 'Foundation',
    color: Color(0xFF5C4033),
    items: [
      _MatItem('Cement',           '50 kg Bag'),
      _MatItem('River Sand',       'm³'),
      _MatItem('Coarse Aggregate', 'm³'),
      _MatItem('Steel Rebar Y10',  'kg'),
      _MatItem('Steel Rebar Y12',  'kg'),
      _MatItem('Binding Wire',     'kg'),
      _MatItem('Formwork Timber',  'm²'),
      _MatItem('Nails',            'kg'),
    ],
  ),
  _ProcessSection(
    icon: Icons.bento_outlined,
    label: 'Masonry / Block Work',
    color: Color(0xFF546E7A),
    items: [
      _MatItem('Hollow Concrete Blocks', 'units'),
      _MatItem('Cement',                 '50 kg Bag'),
      _MatItem('River Sand',             'm³'),
      _MatItem('DPC Sheet',              'm²'),
      _MatItem('Lintel Steel',           'kg'),
    ],
  ),
  _ProcessSection(
    icon: Icons.roofing_outlined,
    label: 'Roofing',
    color: Color(0xFF37474F),
    items: [
      _MatItem('Roofing Sheets',  'm²'),
      _MatItem('Timber Rafters',  'm'),
      _MatItem('Timber Purlins',  'm'),
      _MatItem('Ridge Cap',       'm'),
      _MatItem('Fascia Board',    'm'),
      _MatItem('Roofing Nails',   'kg'),
      _MatItem('Roof Screws',     'units'),
    ],
  ),
  _ProcessSection(
    icon: Icons.format_paint_outlined,
    label: 'Plastering & Rendering',
    color: Color(0xFF6A1B9A),
    items: [
      _MatItem('Cement',      '50 kg Bag'),
      _MatItem('Fine Sand',   'm³'),
      _MatItem('Plasticizer', 'L'),
    ],
  ),
  _ProcessSection(
    icon: Icons.grid_on_outlined,
    label: 'Flooring',
    color: Color(0xFF00695C),
    items: [
      _MatItem('Floor Tiles',    'm²'),
      _MatItem('Tile Adhesive',  'Bag'),
      _MatItem('Cement',         '50 kg Bag'),
      _MatItem('Sand',           'm³'),
      _MatItem('Tile Grout',     'kg'),
      _MatItem('Skirting Tiles', 'm'),
    ],
  ),
  _ProcessSection(
    icon: Icons.door_front_door_outlined,
    label: 'Doors & Windows',
    color: Color(0xFF1565C0),
    items: [
      _MatItem('Door Frames',    'units'),
      _MatItem('Door Leaves',    'units'),
      _MatItem('Window Frames',  'units'),
      _MatItem('Window Glass',   'm²'),
      _MatItem('Hinges',         'Sets'),
      _MatItem('Door Locks',     'units'),
      _MatItem('Window Latches', 'units'),
    ],
  ),
  _ProcessSection(
    icon: Icons.brush_outlined,
    label: 'Painting & Finishing',
    color: Color(0xFFAD1457),
    items: [
      _MatItem('Wall Paint (Interior)',   'L'),
      _MatItem('Ceiling Paint',           'L'),
      _MatItem('Exterior Paint',          'L'),
      _MatItem('Primer',                  'L'),
      _MatItem('Wall Putty',              'kg'),
      _MatItem('Paint Brushes / Rollers', 'Sets'),
    ],
  ),
  _ProcessSection(
    icon: Icons.electrical_services_outlined,
    label: 'Electrical',
    color: Color(0xFFF57F17),
    items: [
      _MatItem('PVC Conduit Pipe',       'm'),
      _MatItem('Electrical Wire',        'm'),
      _MatItem('MCB Distribution Board', 'units'),
      _MatItem('Switches',               'units'),
      _MatItem('Electrical Sockets',     'units'),
      _MatItem('Light Fittings',         'units'),
      _MatItem('Junction Boxes',         'units'),
    ],
  ),
  _ProcessSection(
    icon: Icons.water_outlined,
    label: 'Plumbing',
    color: Color(0xFF0277BD),
    items: [
      _MatItem('PVC Pipes',    'm'),
      _MatItem('PVC Fittings', 'units'),
      _MatItem('Wash Basin',   'units'),
      _MatItem('WC Closet',    'units'),
      _MatItem('Kitchen Sink', 'units'),
      _MatItem('Water Taps',   'units'),
      _MatItem('Shower Set',   'units'),
      _MatItem('Water Tank',   'units'),
    ],
  ),
];

// ─────────────────────────────────────────────────────────────────────────────

class MaterialsTab extends StatelessWidget {
  final String? roomLabel;
  final Map<String, dynamic>? roomData;

  const MaterialsTab({super.key, this.roomLabel, this.roomData});

  @override
  Widget build(BuildContext context) {
    if (roomLabel != null) {
      return _MaterialBlueprintView(
          roomLabel: roomLabel!, roomData: roomData);
    }

    // ── No room selected: existing materials list ─────────────────────
    final pp = context.watch<ProjectProvider>();
    final items = pp.materials;

    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      appBar: AppBar(
        automaticallyImplyLeading: false,
        backgroundColor: const Color(0xFF1565C0),
        foregroundColor: Colors.white,
        elevation: 0,
        title: const Text('Project Materials',
            style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
        actions: [
          Tooltip(
            message: 'Manage Material Library',
            child: IconButton(
              icon: const Icon(Icons.library_books_outlined),
              onPressed: () => Navigator.push(
                context,
                MaterialPageRoute(
                    builder: (_) => const MaterialLibraryScreen()),
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddDialog(context),
        backgroundColor: const Color(0xFF1565C0),
        foregroundColor: Colors.white,
        child: const Icon(Icons.add),
      ),
      body: items.isEmpty
          ? _buildEmpty(context)
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: items.length,
              itemBuilder: (_, i) => _MaterialTile(material: items[i]),
            ),
    );
  }

  Widget _buildEmpty(BuildContext context) => Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.inventory_2_outlined,
                size: 64, color: Colors.grey[300]),
            const SizedBox(height: 12),
            const Text('No materials yet',
                style: TextStyle(fontSize: 16, color: Colors.grey)),
            const SizedBox(height: 8),
            ElevatedButton.icon(
              onPressed: () => _showAddDialog(context),
              icon: const Icon(Icons.add),
              label: const Text('Add Material'),
              style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF1565C0),
                  foregroundColor: Colors.white),
            ),
          ],
        ),
      );

  void _showAddDialog(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => const _AddMaterialSheet(),
    );
  }
}

class _MaterialTile extends StatelessWidget {
  final MaterialModel material;
  const _MaterialTile({required this.material});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      shape:
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      child: ListTile(
        leading: Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: const Color(0xFF1565C0).withAlpha(20),
            borderRadius: BorderRadius.circular(8),
          ),
          child: const Icon(Icons.inventory_2,
              color: Color(0xFF1565C0), size: 20),
        ),
        title: Text(material.materialName,
            style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text('${material.category} · ${material.baseUnit}'),
        trailing: Text(
            '${material.allowedSizes.length} size${material.allowedSizes.length != 1 ? 's' : ''}',
            style: TextStyle(color: Colors.grey[500], fontSize: 12)),
      ),
    );
  }
}

class _AddMaterialSheet extends StatefulWidget {
  const _AddMaterialSheet();
  @override
  State<_AddMaterialSheet> createState() => _AddMaterialSheetState();
}

class _AddMaterialSheetState extends State<_AddMaterialSheet> {
  final _form = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _category = TextEditingController();
  final _unit = TextEditingController();
  bool _saving = false;

  @override
  void dispose() {
    _name.dispose();
    _category.dispose();
    _unit.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
          left: 20,
          right: 20,
          top: 24,
          bottom: MediaQuery.of(context).viewInsets.bottom + 24),
      child: Form(
        key: _form,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Add Material',
                style:
                    TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            _tf(_name, 'Material Name *',
                validator: (v) =>
                    v == null || v.isEmpty ? 'Required' : null),
            _tf(_category, 'Category (e.g. Cement, Steel)'),
            _tf(_unit, 'Unit (e.g. Bag, Kg, m³)'),
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _saving ? null : _save,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF1565C0),
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10)),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                child: _saving
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                            color: Colors.white, strokeWidth: 2))
                    : const Text('Add'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _tf(TextEditingController c, String label,
      {String? Function(String?)? validator}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: TextFormField(
        controller: c,
        validator: validator,
        decoration: InputDecoration(
          labelText: label,
          border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8)),
          contentPadding:
              const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
        ),
      ),
    );
  }

  Future<void> _save() async {
    if (!_form.currentState!.validate()) return;
    setState(() => _saving = true);
    final pp = context.read<ProjectProvider>();
    await pp.addMaterial(MaterialModel(
      materialId: const Uuid().v4(),
      materialName: _name.text.trim(),
      category: _category.text.trim().isEmpty ? 'General' : _category.text.trim(),
      baseUnit: _unit.text.trim().isEmpty ? 'Unit' : _unit.text.trim(),
    ));
    setState(() => _saving = false);
    if (context.mounted) Navigator.pop(context);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Blueprint view: process-by-process material tables
// ─────────────────────────────────────────────────────────────────────────────

class _MaterialBlueprintView extends StatelessWidget {
  final String roomLabel;
  final Map<String, dynamic>? roomData;
  const _MaterialBlueprintView(
      {required this.roomLabel, this.roomData});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      body: ListView(
        padding: const EdgeInsets.all(14),
        children: [
          // ── Room header card ──────────────────────────────────────────
          Container(
            margin: const EdgeInsets.only(bottom: 14),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFF1565C0),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(children: [
              const Icon(Icons.meeting_room_outlined,
                  color: Colors.white, size: 22),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Materials Blueprint',
                        style: TextStyle(
                            color: Colors.white70, fontSize: 11)),
                    Text(roomLabel,
                        style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.white.withAlpha(30),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Text('Qty: pending',
                    style: TextStyle(
                        color: Colors.white70, fontSize: 11)),
              ),
              const SizedBox(width: 8),
              Tooltip(
                message: 'Manage Material Library',
                child: InkWell(
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (_) => const MaterialLibraryScreen()),
                  ),
                  borderRadius: BorderRadius.circular(20),
                  child: Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: Colors.white.withAlpha(30),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Icon(Icons.library_books_outlined,
                        size: 18, color: Colors.white),
                  ),
                ),
              ),
            ]),
          ),

          // ── Process sections ──────────────────────────────────────────
          for (final section in _kBlueprint) ...[
            _ProcessCard(section: section),
            const SizedBox(height: 10),
          ],

          const SizedBox(height: 24),
        ],
      ),
    );
  }
}

// ─── Process section card ─────────────────────────────────────────────────────

class _ProcessCard extends StatelessWidget {
  final _ProcessSection section;
  const _ProcessCard({required this.section});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withAlpha(12),
              blurRadius: 6,
              offset: const Offset(0, 2))
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Section header
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: section.color.withAlpha(20),
              borderRadius:
                  const BorderRadius.vertical(top: Radius.circular(12)),
              border: Border(
                  bottom: BorderSide(
                      color: section.color.withAlpha(40), width: 1)),
            ),
            child: Row(children: [
              Icon(section.icon, size: 18, color: section.color),
              const SizedBox(width: 8),
              Text(section.label,
                  style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                      color: section.color)),
            ]),
          ),

          // Scrollable table
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 14),
            child: ConstrainedBox(
              constraints: const BoxConstraints(minWidth: 560),
              child: Column(
                children: [
                  // Column headers row
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    child: Row(children: [
                      const SizedBox(width: 160,
                          child: Text('Material',
                              style: TextStyle(fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  color: Color(0xFF757575)))),
                      const SizedBox(width: 12),
                      const SizedBox(width: 60,
                          child: Text('Unit',
                              style: TextStyle(fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  color: Color(0xFF757575)))),
                      const SizedBox(width: 12),
                      const SizedBox(width: 70,
                          child: Text('Quantity',
                              textAlign: TextAlign.center,
                              style: TextStyle(fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  color: Color(0xFF757575)))),
                      const SizedBox(width: 12),
                      const SizedBox(width: 100,
                          child: Text('Brand',
                              textAlign: TextAlign.center,
                              style: TextStyle(fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  color: Color(0xFF757575)))),
                      const SizedBox(width: 12),
                      const SizedBox(width: 100,
                          child: Text('Size',
                              textAlign: TextAlign.center,
                              style: TextStyle(fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  color: Color(0xFF757575)))),
                    ]),
                  ),
                  const Divider(height: 1),
                  for (int i = 0; i < section.items.length; i++)
                    _MatRow(
                        item: section.items[i],
                        isLast: i == section.items.length - 1),
                ],
              ),
            ),
          ),

          const SizedBox(height: 4),
        ],
      ),
    );
  }
}

class _MatRow extends StatefulWidget {
  final _MatItem item;
  final bool isLast;
  const _MatRow({required this.item, required this.isLast});

  @override
  State<_MatRow> createState() => _MatRowState();
}

class _MatRowState extends State<_MatRow> {
  String? _selectedBrand;
  String? _selectedSize;

  // Cache so we only call the API once per row
  List<String>? _brands;
  List<String>? _sizes;
  bool _loadingOptions = false;

  Future<Map<String, List<String>>> _fetchOptions() async {
    if (_brands != null && _sizes != null) {
      return {'brands': _brands!, 'sizes': _sizes!};
    }
    setState(() => _loadingOptions = true);
    try {
      final api = MongoApiService();
      await api.loadToken();
      final res = await api.getMaterialOptions(widget.item.name);
      _brands = List<String>.from(res['brands'] as List? ?? []);
      _sizes  = List<String>.from(res['sizes']  as List? ?? []);
    } catch (_) {
      _brands = [];
      _sizes  = [];
    } finally {
      if (mounted) setState(() => _loadingOptions = false);
    }
    return {'brands': _brands!, 'sizes': _sizes!};
  }

  Future<void> _pickBrand() async {
    final opts = await _fetchOptions();
    if (!mounted) return;
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
      builder: (_) => _BrandSelectSheet(
        title: 'Select Brand — ${widget.item.name}',
        brands: opts['brands']!,
        onSelected: (v) => setState(() => _selectedBrand = v),
      ),
    );
  }

  Future<void> _pickSize() async {
    final opts = await _fetchOptions();
    if (!mounted) return;
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
      builder: (_) => _SelectSheet(
        title: 'Select Size — ${widget.item.name}',
        options: opts['sizes']!,
        onSelected: (v) => setState(() => _selectedSize = v),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(children: [
            // Material thumbnail
            _MatThumbnail(name: widget.item.name),
            const SizedBox(width: 8),
            // Material name
            SizedBox(
              width: 130,
              child: Text(widget.item.name,
                  style: const TextStyle(fontSize: 12)),
            ),
            const SizedBox(width: 12),
            // Unit
            SizedBox(
              width: 60,
              child: Text(widget.item.unit,
                  style: TextStyle(
                      fontSize: 11, color: Colors.grey[600])),
            ),
            const SizedBox(width: 12),
            // Quantity placeholder
            SizedBox(
              width: 70,
              child: Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 6, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFFF5F7FA),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(
                      color: Colors.grey.withAlpha(60), width: 1),
                ),
                alignment: Alignment.center,
                child: const Text('—',
                    style:
                        TextStyle(fontSize: 12, color: Colors.grey)),
              ),
            ),
            const SizedBox(width: 12),
            // Brand select
            SizedBox(
              width: 100,
              child: _loadingOptions
                  ? _loadingCell()
                  : _selectedBrand == null
                      ? _selectBtn('Select', onTap: _pickBrand)
                      : _selectedChip(_selectedBrand!, onTap: _pickBrand),
            ),
            const SizedBox(width: 12),
            // Size select
            SizedBox(
              width: 100,
              child: _loadingOptions
                  ? _loadingCell()
                  : _selectedSize == null
                      ? _selectBtn('Select', onTap: _pickSize)
                      : _selectedChip(_selectedSize!, onTap: _pickSize),
            ),
          ]),
          ),
        ),
        if (!widget.isLast) const Divider(height: 1),
      ],
    );
  }

  Widget _loadingCell() => Container(
        height: 28,
        alignment: Alignment.center,
        child: const SizedBox(
          width: 14,
          height: 14,
          child: CircularProgressIndicator(
              strokeWidth: 1.5, color: Color(0xFF1565C0)),
        ),
      );

  Widget _selectBtn(String label, {required VoidCallback onTap}) =>
      GestureDetector(
        onTap: onTap,
        child: Container(
          padding:
              const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
          decoration: BoxDecoration(
            border: Border.all(
                color: const Color(0xFF1565C0).withAlpha(150), width: 1),
            borderRadius: BorderRadius.circular(6),
          ),
          alignment: Alignment.center,
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            const Icon(Icons.arrow_drop_down,
                size: 14, color: Color(0xFF1565C0)),
            const SizedBox(width: 2),
            Text(label,
                style: const TextStyle(
                    fontSize: 11,
                    color: Color(0xFF1565C0),
                    fontWeight: FontWeight.w500)),
          ]),
        ),
      );

  Widget _selectedChip(String value, {required VoidCallback onTap}) =>
      GestureDetector(
        onTap: onTap,
        child: Container(
          padding:
              const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
          decoration: BoxDecoration(
            color: const Color(0xFF1565C0).withAlpha(18),
            border: Border.all(
                color: const Color(0xFF1565C0).withAlpha(80), width: 1),
            borderRadius: BorderRadius.circular(6),
          ),
          alignment: Alignment.center,
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            Flexible(
              child: Text(value,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                      fontSize: 11,
                      color: Color(0xFF1565C0),
                      fontWeight: FontWeight.w600)),
            ),
            const SizedBox(width: 2),
            const Icon(Icons.edit_outlined,
                size: 11, color: Color(0xFF1565C0)),
          ]),
        ),
      );
}

// ─── Material thumbnail widget ───────────────────────────────────────────────

class _MatThumbnail extends StatelessWidget {
  final String name;
  const _MatThumbnail({required this.name});

  @override
  Widget build(BuildContext context) {
    final path = _matImagePath(name);
    if (path != null) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(6),
        child: Image.asset(path,
            width: 32, height: 32,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => _placeholder()),
      );
    }
    return _placeholder();
  }

  Widget _placeholder() {
    return Container(
      width: 32, height: 32,
      decoration: BoxDecoration(
        color: const Color(0xFF1565C0).withAlpha(20),
        borderRadius: BorderRadius.circular(6),
      ),
      alignment: Alignment.center,
      child: Text(
        name.isNotEmpty ? name[0].toUpperCase() : '?',
        style: const TextStyle(
            fontSize: 13, fontWeight: FontWeight.bold,
            color: Color(0xFF1565C0)),
      ),
    );
  }
}

// ─── Brand select bottom-sheet (shows logo tiles) ─────────────────────────────

class _BrandSelectSheet extends StatelessWidget {
  final String title;
  final List<String> brands;
  final void Function(String) onSelected;
  const _BrandSelectSheet(
      {required this.title, required this.brands, required this.onSelected});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(
          20, 20, 20, MediaQuery.of(context).viewInsets.bottom + 28),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style: const TextStyle(
                  fontSize: 14, fontWeight: FontWeight.bold)),
          const SizedBox(height: 14),
          if (brands.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 12),
              child: Text('No brands available for this material.',
                  style: TextStyle(color: Colors.grey)),
            )
          else
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: brands.map((brand) {
                final logo = _brandLogoPath(brand);
                return GestureDetector(
                  onTap: () {
                    onSelected(brand);
                    Navigator.pop(context);
                  },
                  child: Container(
                    width: 90,
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                          color: const Color(0xFF1565C0).withAlpha(60)),
                      boxShadow: [BoxShadow(
                          color: Colors.black.withAlpha(8),
                          blurRadius: 4, offset: const Offset(0, 2))],
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (logo != null)
                          Image.asset(logo,
                              height: 44, width: double.infinity,
                              fit: BoxFit.contain,
                              errorBuilder: (_, __, ___) =>
                                  const Icon(Icons.business_outlined,
                                      size: 36, color: Color(0xFF1565C0)))
                        else
                          const Icon(Icons.business_outlined,
                              size: 36, color: Color(0xFF1565C0)),
                        const SizedBox(height: 6),
                        Text(brand,
                            textAlign: TextAlign.center,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                                color: Color(0xFF1565C0))),
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}

// ─── Size select bottom-sheet (text chips) ────────────────────────────────────

class _SelectSheet extends StatelessWidget {
  final String title;
  final List<String> options;
  final void Function(String) onSelected;
  const _SelectSheet(
      {required this.title,
      required this.options,
      required this.onSelected});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 28),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style: const TextStyle(
                  fontSize: 14, fontWeight: FontWeight.bold)),
          const SizedBox(height: 14),
          if (options.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 12),
              child: Text('No sizes available for this material.',
                  style: TextStyle(color: Colors.grey)),
            )
          else
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: options
                  .map((o) => ActionChip(
                        label: Text(o),
                        onPressed: () {
                          onSelected(o);
                          Navigator.pop(context);
                        },
                        backgroundColor:
                            const Color(0xFF1565C0).withAlpha(15),
                        side: BorderSide(
                            color: const Color(0xFF1565C0).withAlpha(80)),
                        labelStyle: const TextStyle(
                            color: Color(0xFF1565C0), fontSize: 13),
                      ))
                  .toList(),
            ),
        ],
      ),
    );
  }
}

// ─── Data models ──────────────────────────────────────────────────────────────

class _ProcessSection {
  final IconData icon;
  final String label;
  final Color color;
  final List<_MatItem> items;
  const _ProcessSection(
      {required this.icon,
      required this.label,
      required this.color,
      required this.items});
}

class _MatItem {
  final String name;
  final String unit;
  const _MatItem(this.name, this.unit);
}
