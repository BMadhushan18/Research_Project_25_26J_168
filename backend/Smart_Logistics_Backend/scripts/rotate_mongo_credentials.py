"""Rotate/update MongoDB URI in local .env file (development convenience).
This simply replaces the MONGODB_URI line in the .env file. It does NOT change credentials on the DB server.
Usage:
  python scripts/rotate_mongo_credentials.py --uri "mongodb+srv://user:pass@cluster0..."
"""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--uri', required=True)
parser.add_argument('--env', default='.env')
args = parser.parse_args()

p = Path(args.env)
lines = []
if p.exists():
    lines = p.read_text().splitlines()
new_lines = []
found = False
for ln in lines:
    if ln.startswith('MONGODB_URI='):
        new_lines.append(f'MONGODB_URI={args.uri}')
        found = True
    else:
        new_lines.append(ln)
if not found:
    new_lines.append(f'MONGODB_URI={args.uri}')
p.write_text('\n'.join(new_lines))
print(f'Updated {p} with new MONGODB_URI')
