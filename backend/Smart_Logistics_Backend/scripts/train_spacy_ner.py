import json
import random
from pathlib import Path
import spacy
from spacy.tokens import DocBin
from spacy.training import Example

ROOT = Path(__file__).resolve().parents[1]
ANN_PATH = ROOT / 'data' / 'nlp' / 'annotations.json'
OUT_DIR = ROOT / 'ml' / 'spacy_ner_v1'


def load_annotations(path):
    with open(path, 'r', encoding='utf-8') as f:
        anns = json.load(f)
    return anns


def make_docbin(nlp, examples):
    docbin = DocBin()
    for text, entities in examples:
        doc = nlp.make_doc(text)
        ents = []
        for (start, end, label) in entities:
            span = doc.char_span(start, end, label=label, alignment_mode='contract')
            if span is None:
                # skip malformed spans
                continue
            ents.append(span)
        doc.ents = ents
        docbin.add(doc)
    return docbin


def prepare_data(annotations, split=0.8):
    data = []
    for a in annotations:
        text = a['text']
        ents = [(s, e, l) for (s, e, l) in a['entities']]
        data.append((text, ents))
    random.shuffle(data)
    cutoff = int(len(data) * split)
    return data[:cutoff], data[cutoff:]


def train_ner(annotations_path, out_dir, n_iter=20):
    anns = load_annotations(annotations_path)
    train_data, dev_data = prepare_data(anns)
    # Create blank model
    nlp = spacy.blank('en')
    if 'ner' not in nlp.pipe_names:
        ner = nlp.add_pipe('ner')
    else:
        ner = nlp.get_pipe('ner')
    # add labels
    labels = set([lbl for _, ex in train_data for (_, _, lbl) in ex])
    for l in labels:
        ner.add_label(l)
    # begin training
    optimizer = nlp.begin_training()
    for itn in range(n_iter):
        random.shuffle(train_data)
        losses = {}
        for text, entities in train_data:
            doc = nlp.make_doc(text)
            example = Example.from_dict(doc, {'entities': [(s, e, l) for (s, e, l) in entities]})
            nlp.update([example], sgd=optimizer, drop=0.2, losses=losses)
        print(f"Iteration {itn+1}/{n_iter} - Losses: {losses}")
    # Save model
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(out_dir)
    print('Saved spaCy NER model to', out_dir)
    # Simple evaluation on dev set
    tp = fp = fn = 0
    for text, entities in dev_data:
        doc = nlp(text)
        pred_ents = {(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents}
        gold_ents = {(s, e, l) for (s, e, l) in entities}
        tp += len(pred_ents & gold_ents)
        fp += len(pred_ents - gold_ents)
        fn += len(gold_ents - pred_ents)
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
    print(f"Dev precision={prec:.3f}, recall={rec:.3f}, f1={f1:.3f}")
    return out_dir


if __name__ == '__main__':
    train_ner(ANN_PATH, OUT_DIR, n_iter=15)
