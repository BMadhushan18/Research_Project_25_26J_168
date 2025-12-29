import json
import re
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
ANN_PATH = ROOT / 'data' / 'nlp' / 'annotations.json'
BACKUP_PATH = ROOT / 'data' / 'nlp' / 'annotations.json.bak'

LINE_NAME_RE = re.compile(r"^\s*(?P<name>[A-Za-z ]+?)\s*-\s*")


def fix_annotations(path, backup_path, threshold=0.8):
    with open(path, 'r', encoding='utf-8') as f:
        anns = json.load(f)

    updated = 0
    skipped = 0
    total_old_entities = 0
    total_new_entities = 0
    new_anns = []

    for doc in anns:
        text = doc.get('text', '')
        # normalize escaped-newline sequences to actual newlines (some annotations use literal '\\n')
        text = text.replace('\\n', '\n')
        orig_entities = doc.get('entities', [])
        total_old_entities += len(orig_entities)

        # parse lines and compute material name spans
        lines = text.splitlines(keepends=True)
        new_entities = []
        pos = 0
        for line in lines:
            m = LINE_NAME_RE.match(line)
            if m:
                start = pos + m.start('name')
                end = pos + m.end('name')
                new_entities.append([start, end, 'MATERIAL_NAME'])
            pos += len(line)

        total_new_entities += len(new_entities)

        # acceptance check: only accept if new count >= threshold * old count
        if len(orig_entities) == 0:
            # nothing to do
            new_anns.append(doc)
            skipped += 1
            continue

        if len(new_entities) >= max(1, int(len(orig_entities) * threshold)):
            # apply fix (also store normalized text)
            doc['entities'] = new_entities
            doc['text'] = text
            new_anns.append(doc)
            updated += 1
        else:
            # too different; skip conservative
            new_anns.append(doc)
            skipped += 1

    # make a backup
    shutil.copy2(path, backup_path)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(new_anns, f, indent=2)

    print(f"Processed {len(anns)} docs. Updated: {updated}, Skipped: {skipped}")
    print(f"Total old entities: {total_old_entities}, total new entities: {total_new_entities}")
    print(f"Backup created at: {backup_path}")


if __name__ == '__main__':
    fix_annotations(ANN_PATH, BACKUP_PATH)
