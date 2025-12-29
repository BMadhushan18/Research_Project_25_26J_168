import json,re
LINE_NAME_RE=re.compile(r"^\s*(?P<name>[A-Za-z ]+?)\s*-\s*")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
with open(ROOT / 'data' / 'nlp' / 'annotations.json','r',encoding='utf-8') as f:
    anns=json.load(f)
for i in range(3):
    d=anns[i]
    print('DOC',i)
    text = d['text'].replace('\\n','\n')
    lines=text.splitlines(True)
    for j,line in enumerate(lines):
        m=LINE_NAME_RE.match(line)
        print(' line',j,'len',len(line),'repr',repr(line[:30]),'match',bool(m), 'group' , (m.group('name') if m else None))
    print('orig ents',len(d['entities']))
