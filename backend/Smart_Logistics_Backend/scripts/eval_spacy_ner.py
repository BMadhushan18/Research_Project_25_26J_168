import json
from pathlib import Path
import spacy
from spacy.training import Example
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
ANN_PATH = ROOT / 'data' / 'nlp' / 'annotations.json'
MODEL_DIR = ROOT / 'ml' / 'spacy_ner_v1'


def load_annotations(path):
    with open(path, 'r', encoding='utf-8') as f:
        anns = json.load(f)
    return anns


def prepare_data(annotations, split=0.8):
    data = []
    for a in annotations:
        text = a['text']
        ents = [(s, e, l) for (s, e, l) in a['entities']]
        data.append((text, ents))
    # deterministic order for reporting
    cutoff = int(len(data) * split)
    return data[:cutoff], data[cutoff:]


if __name__ == '__main__':
    anns = load_annotations(ANN_PATH)
    train_data, dev_data = prepare_data(anns)
    print(f"Loaded {len(anns)} annotations ({len(train_data)} train / {len(dev_data)} dev)")

    # load model
    nlp = spacy.load(str(MODEL_DIR))

    # detect misaligned entities in annotations
    misaligned = []
    for i, (text, entities) in enumerate(dev_data):
        doc = nlp.make_doc(text)
        for (s, e, label) in entities:
            span = doc.char_span(s, e, label=label, alignment_mode='contract')
            if span is None:
                misaligned.append({'idx': i, 'text': text, 'entity': (s, e, label), 'snippet': text[max(0, s-20):e+20]})

    print(f"Found {len(misaligned)} misaligned entity annotations in dev set")
    if len(misaligned) > 0:
        print("Sample misaligned annotations (first 10):")
        for m in misaligned[:10]:
            s, e, lab = m['entity']
            print('---')
            print(f"idx={m['idx']} label={lab} span=({s},{e})")
            print(f"text: {repr(m['text'])}")
            print(f"snippet: {repr(m['snippet'])}")

    # simple per-label counts and evaluation
    per_label = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0})
    total_tp = total_fp = total_fn = 0
    for text, entities in dev_data:
        doc = nlp(text)
        pred_ents = {(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents}
        gold_ents = {(s, e, l) for (s, e, l) in entities}
        tp = pred_ents & gold_ents
        fp = pred_ents - gold_ents
        fn = gold_ents - pred_ents
        total_tp += len(tp)
        total_fp += len(fp)
        total_fn += len(fn)
        for (s, e, l) in tp:
            per_label[l]['tp'] += 1
        for (s, e, l) in fp:
            per_label[l]['fp'] += 1
        for (s, e, l) in fn:
            per_label[l]['fn'] += 1

    def safe_div(a, b):
        return a / b if b > 0 else 0.0

    print('\nOverall dev set metrics:')
    prec = safe_div(total_tp, total_tp + total_fp)
    rec = safe_div(total_tp, total_tp + total_fn)
    f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
    print(f"Precision={prec:.3f}, Recall={rec:.3f}, F1={f1:.3f} (TP={total_tp} FP={total_fp} FN={total_fn})")

    print('\nPer-label metrics:')
    for label, counts in per_label.items():
        tp = counts['tp']
        fp = counts['fp']
        fn = counts['fn']
        p = safe_div(tp, tp + fp)
        r = safe_div(tp, tp + fn)
        f = 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0
        print(f"{label}: P={p:.3f} R={r:.3f} F1={f:.3f} (TP={tp} FP={fp} FN={fn})")

    # show some FN examples
    print('\nSample false-negative (missed) examples (first 10):')
    fn_examples_shown = 0
    for text, entities in dev_data:
        doc = nlp(text)
        pred_ents = {(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents}
        gold_ents = {(s, e, l) for (s, e, l) in entities}
        missed = gold_ents - pred_ents
        if missed and fn_examples_shown < 10:
            print('---')
            print(f"text: {repr(text)}")
            print(f"missed: {missed}")
            fn_examples_shown += 1

    print('\nEvaluation complete.')
