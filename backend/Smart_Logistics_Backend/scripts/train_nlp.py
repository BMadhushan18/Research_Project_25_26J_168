import json
from pathlib import Path
import spacy
from spacy.tokens import DocBin

ROOT = Path(__file__).resolve().parents[1]
NLP_DATA = ROOT / "data" / "nlp"
ML_DIR = ROOT / "ml"
ML_DIR.mkdir(parents=True, exist_ok=True)


def create_training_data(annotations_path):
    with open(annotations_path, 'r', encoding='utf-8') as f:
        anns = json.load(f)
    TRAIN = []
    for a in anns:
        text = a['text']
        ents = []
        for (start,end,label) in a['entities']:
            ents.append((start,end,label))
        TRAIN.append((text, {'entities': ents}))
    return TRAIN


def train():
    TRAIN = create_training_data(NLP_DATA / 'annotations.json')
    # Use EntityRuler for quick deterministic training
    nlp = spacy.blank('en')
    ruler = nlp.add_pipe('entity_ruler')
    patterns = []
    for text, ann in TRAIN[:200]:
        for s,e,l in ann['entities']:
            patterns.append({"label": l, "pattern": text[s:e]})
    ruler.add_patterns(patterns)
    # Save model
    nlp.to_disk(ML_DIR / 'spacy_doc_extractor_v1')
    print('Saved spaCy rule-based extractor to', ML_DIR / 'spacy_doc_extractor_v1')

if __name__ == '__main__':
    train()