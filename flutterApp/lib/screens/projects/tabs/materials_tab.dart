import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';
import '../../../providers/mongo_auth_provider.dart';
import '../../../providers/mongo_project_provider.dart';
import '../../../models/project/material_model.dart';

class MaterialsTab extends StatelessWidget {
  const MaterialsTab({super.key});

  @override
  Widget build(BuildContext context) {
    final pp = context.watch<ProjectProvider>();
    final items = pp.materials;

    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
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
