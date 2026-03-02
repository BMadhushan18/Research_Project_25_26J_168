import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';
import '../../../providers/mongo_project_provider.dart';
import '../../../models/project/boq_model.dart';

class BOQTab extends StatelessWidget {
  const BOQTab({super.key});

  @override
  Widget build(BuildContext context) {
    final pp = context.watch<ProjectProvider>();
    final items = pp.boqItems;
    final currency =
        pp.currentProject?.currency ?? 'LKR';

    // Group by section
    final Map<String, List<BOQItem>> grouped = {};
    for (final item in items) {
      final key = item.section ?? 'General';
      grouped.putIfAbsent(key, () => []).add(item);
    }

    double total = items.fold(0, (s, i) => s + (i.computedAmount));

    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAdd(context),
        backgroundColor: const Color(0xFF1565C0),
        foregroundColor: Colors.white,
        child: const Icon(Icons.add),
      ),
      body: items.isEmpty
          ? _Empty(onAdd: () => _showAdd(context))
          : Column(
              children: [
                // Total banner
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(14),
                  color: const Color(0xFF1565C0),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('BOQ Total',
                          style: TextStyle(
                              color: Colors.white70, fontSize: 13)),
                      Text(
                        '$currency ${total.toStringAsFixed(2)}',
                        style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 18),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: grouped.entries.map((entry) {
                      final sectionTotal = entry.value
                          .fold<double>(0, (s, i) => s + i.computedAmount);
                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 10, vertical: 6),
                            decoration: BoxDecoration(
                              color: const Color(0xFF1565C0).withAlpha(20),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Row(
                              mainAxisAlignment:
                                  MainAxisAlignment.spaceBetween,
                              children: [
                                Text(entry.key,
                                    style: const TextStyle(
                                        fontWeight: FontWeight.bold,
                                        fontSize: 13)),
                                Text(
                                    '$currency ${sectionTotal.toStringAsFixed(0)}',
                                    style: const TextStyle(
                                        fontSize: 12,
                                        color: Color(0xFF1565C0),
                                        fontWeight: FontWeight.bold)),
                              ],
                            ),
                          ),
                          ...entry.value.map((i) => _BOQTile(
                              item: i, currency: currency)),
                          const SizedBox(height: 8),
                        ],
                      );
                    }).toList(),
                  ),
                ),
              ],
            ),
    );
  }

  void _showAdd(BuildContext context) => showModalBottomSheet(
        context: context,
        isScrollControlled: true,
        shape: const RoundedRectangleBorder(
            borderRadius:
                BorderRadius.vertical(top: Radius.circular(20))),
        builder: (_) => const _AddBOQSheet(),
      );
}

class _BOQTile extends StatelessWidget {
  final BOQItem item;
  final String currency;
  const _BOQTile({required this.item, required this.currency});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(top: 6),
      shape:
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(item.description,
                      style: const TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 3),
                  Text(
                    '${item.qty} ${item.unit}  ×  $currency ${item.unitRate?.toStringAsFixed(2) ?? '0.00'}',
                      style: TextStyle(
                          fontSize: 12, color: Colors.grey[600])),
                ],
              ),
            ),
            Text(
              '$currency ${item.computedAmount.toStringAsFixed(2)}',
              style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1565C0)),
            ),
          ],
        ),
      ),
    );
  }
}

class _Empty extends StatelessWidget {
  final VoidCallback onAdd;
  const _Empty({required this.onAdd});
  @override
  Widget build(BuildContext context) => Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.format_list_numbered,
                size: 64, color: Colors.grey[300]),
            const SizedBox(height: 12),
            const Text('No BOQ items yet',
                style: TextStyle(fontSize: 16, color: Colors.grey)),
            const SizedBox(height: 8),
            ElevatedButton.icon(
              onPressed: onAdd,
              icon: const Icon(Icons.add),
              label: const Text('Add BOQ Item'),
              style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF1565C0),
                  foregroundColor: Colors.white),
            ),
          ],
        ),
      );
}

class _AddBOQSheet extends StatefulWidget {
  const _AddBOQSheet();
  @override
  State<_AddBOQSheet> createState() => _AddBOQSheetState();
}

class _AddBOQSheetState extends State<_AddBOQSheet> {
  final _form = GlobalKey<FormState>();
  final _desc = TextEditingController();
  final _unit = TextEditingController();
  final _qty = TextEditingController();
  final _rate = TextEditingController();
  final _section = TextEditingController();
  bool _saving = false;

  @override
  void dispose() {
    _desc.dispose();
    _unit.dispose();
    _qty.dispose();
    _rate.dispose();
    _section.dispose();
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
            const Text('Add BOQ Item',
                style:
                    TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            _tf(_desc, 'Description *',
                validator: (v) =>
                    v == null || v.isEmpty ? 'Required' : null),
            _tf(_section, 'Section (e.g. Substructure)'),
            Row(
              children: [
                Expanded(child: _tf(_unit, 'Unit *')),
                const SizedBox(width: 10),
                Expanded(
                    child: _tf(_qty, 'Quantity *',
                        keyboardType: TextInputType.number)),
              ],
            ),
            _tf(_rate, 'Unit Rate *', keyboardType: TextInputType.number,
                validator: (v) =>
                    v == null || v.isEmpty ? 'Required' : null),
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
      {String? Function(String?)? validator,
      TextInputType? keyboardType}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: TextFormField(
        controller: c,
        validator: validator,
        keyboardType: keyboardType,
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
    await pp.addBOQItem(BOQItem(
      boqItemId: const Uuid().v4(),
      description: _desc.text.trim(),
      unit: _unit.text.trim().isEmpty ? 'No.' : _unit.text.trim(),
      qty: double.tryParse(_qty.text.trim()) ?? 1,
      unitRate: double.tryParse(_rate.text.trim()) ?? 0,
      section: _section.text.trim().isEmpty ? 'General' : _section.text.trim(),
    ));
    setState(() => _saving = false);
    if (context.mounted) Navigator.pop(context);
  }
}
