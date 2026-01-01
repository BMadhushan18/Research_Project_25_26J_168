"""Export predictions logged in MongoDB to CSV.
Usage:
  python scripts/export_predictions.py --out exports/predictions.csv --limit 1000
"""
import argparse
import csv
from datetime import datetime
from app.db import get_db

parser = argparse.ArgumentParser()
parser.add_argument('--out', default='exports/predictions.csv')
parser.add_argument('--limit', type=int, default=10000)
parser.add_argument('--filter', type=str, default=None, help='Optional JSON filter string (e.g. "{\"labour_roles\":\"mason\"}")')
args = parser.parse_args()

db = get_db()
if db is None:
    raise SystemExit('MongoDB not available; set MONGODB_URI and ensure connectivity')

query = {}
if args.filter:
    import json
    query = json.loads(args.filter)

cursor = db.predictions.find(query).sort('created_at', -1).limit(args.limit)

PathExists = False
with open(args.out, 'w', newline='', encoding='utf-8') as csvfile:
    writer = None
    count = 0
    for doc in cursor:
        doc.pop('_id', None)
        # flatten certain nested fields
        row = {
            'created_at': doc.get('created_at'),
            'raw_text': doc.get('raw_text'),
            'materials': '|'.join([str(m) for m in doc.get('materials', [])]),
            'prediction': str(doc.get('prediction'))
        }
        if writer is None:
            writer = csv.DictWriter(csvfile, fieldnames=list(row.keys()))
            writer.writeheader()
        writer.writerow(row)
        count += 1

print(f'Exported {count} predictions to {args.out}')
