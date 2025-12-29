import shutil
from pathlib import Path
from datetime import datetime
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'backend' / 'Smart_Logistics_Backend'
OUT_DIR = ROOT / 'backups'
OUT_DIR.mkdir(exist_ok=True)
now = datetime.now().strftime('%Y%m%d_%H%M%S')
archive_name = OUT_DIR / f'Smart_Logistics_Backend_backup_{now}'
shutil.make_archive(str(archive_name), 'zip', root_dir=str(SRC))
print('Created backup:', str(archive_name) + '.zip')
