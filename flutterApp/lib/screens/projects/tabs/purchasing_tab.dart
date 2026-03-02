import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../providers/mongo_project_provider.dart';
import '../../../models/project/purchasing_model.dart';

class PurchasingTab extends StatelessWidget {
  const PurchasingTab({super.key});

  @override
  Widget build(BuildContext context) {
    final pp = context.watch<ProjectProvider>();
    final pos = pp.pos;
    final currency = pp.currentProject?.currency ?? 'LKR';

    return DefaultTabController(
      length: 3,
      child: Scaffold(
        backgroundColor: const Color(0xFFF5F7FA),
        appBar: PreferredSize(
          preferredSize: const Size.fromHeight(48),
          child: Container(
            color: Colors.white,
            child: const TabBar(
              labelColor: Color(0xFF1565C0),
              unselectedLabelColor: Colors.grey,
              indicatorColor: Color(0xFF1565C0),
              tabs: [
                Tab(text: 'Purchase Orders'),
                Tab(text: 'GRNs'),
                Tab(text: 'Invoices'),
              ],
            ),
          ),
        ),
        body: TabBarView(
          children: [
            _POList(pos: pos, currency: currency),
            _GRNList(grns: pp.grns, currency: currency),
            _InvoiceList(invoices: pp.invoices, currency: currency),
          ],
        ),
      ),
    );
  }
}

// ─── PO List ──────────────────────────────────────────────────────────────────
class _POList extends StatelessWidget {
  final List<PurchaseOrder> pos;
  final String currency;
  const _POList({required this.pos, required this.currency});

  @override
  Widget build(BuildContext context) {
    if (pos.isEmpty) {
      return _centred('No purchase orders yet', Icons.shopping_cart_outlined);
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: pos.length,
      itemBuilder: (_, i) {
        final po = pos[i];
        final total = po.lines
            .fold<double>(0, (s, l) => s + (l.qty ?? 0) * (l.unitPrice ?? 0));
        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          child: ListTile(
            leading: const Icon(Icons.receipt_long,
                color: Color(0xFF1565C0)),
            title: Text(po.poId,
                style: const TextStyle(fontWeight: FontWeight.w600)),
            subtitle: Text(po.supplierId ?? '—'),
            trailing: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text('$currency ${total.toStringAsFixed(0)}',
                    style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF1565C0))),
                _StatusChip(po.status ?? 'Draft'),
              ],
            ),
          ),
        );
      },
    );
  }
}

// ─── GRN List ─────────────────────────────────────────────────────────────────
class _GRNList extends StatelessWidget {
  final List<GRN> grns;
  final String currency;
  const _GRNList({required this.grns, required this.currency});

  @override
  Widget build(BuildContext context) {
    if (grns.isEmpty) {
      return _centred('No GRNs yet', Icons.local_shipping_outlined);
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: grns.length,
      itemBuilder: (_, i) {
        final grn = grns[i];
        final date = grn.date != null
            ? '${grn.date!.day}/${grn.date!.month}/${grn.date!.year}'
            : '—';
        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10)),
          child: ListTile(
            leading: const Icon(Icons.local_shipping,
                color: Colors.green),
            title: Text(grn.grnId,
                style: const TextStyle(fontWeight: FontWeight.w600)),
            subtitle: Text('Received: $date'),
            trailing: Text('${grn.lines.length} items',
                style: TextStyle(
                    color: Colors.grey[600], fontSize: 12)),
          ),
        );
      },
    );
  }
}

// ─── Invoice List ─────────────────────────────────────────────────────────────
class _InvoiceList extends StatelessWidget {
  final List<SupplierInvoice> invoices;
  final String currency;
  const _InvoiceList(
      {required this.invoices, required this.currency});

  @override
  Widget build(BuildContext context) {
    if (invoices.isEmpty) {
      return _centred('No invoices yet', Icons.description_outlined);
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: invoices.length,
      itemBuilder: (_, i) {
        final inv = invoices[i];
        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10)),
          child: ListTile(
            leading: const Icon(Icons.description,
                color: Colors.orange),
            title: Text(inv.invoiceId,
                style: const TextStyle(fontWeight: FontWeight.w600)),
            subtitle: Text(inv.supplierId ?? '—'),
            trailing: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                if (inv.totalPayable != null)
                  Text(
                      '$currency ${inv.totalPayable!.toStringAsFixed(0)}',
                      style: const TextStyle(
                          fontWeight: FontWeight.bold)),
                _StatusChip(inv.status),
              ],
            ),
          ),
        );
      },
    );
  }
}

// ─── Helpers ─────────────────────────────────────────────────────────────────
Widget _centred(String text, IconData icon) => Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 64, color: Colors.grey[300]),
          const SizedBox(height: 12),
          Text(text,
              style: const TextStyle(fontSize: 16, color: Colors.grey)),
        ],
      ),
    );

class _StatusChip extends StatelessWidget {
  final String status;
  const _StatusChip(this.status);

  Color get _color {
    switch (status.toLowerCase()) {
      case 'approved':
      case 'paid':
      case 'completed':
        return Colors.green;
      case 'draft':
      case 'pending':
        return Colors.orange;
      case 'cancelled':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) => Container(
        padding:
            const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
        decoration: BoxDecoration(
          color: _color.withAlpha(25),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Text(status,
            style: TextStyle(
                fontSize: 10,
                color: _color,
                fontWeight: FontWeight.bold)),
      );
}
