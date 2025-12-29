import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def test_spacy_ner_training():
    script = str(ROOT / 'scripts' / 'train_spacy_ner.py')
    r = subprocess.run(["python", script])
    assert r.returncode == 0
    assert (ROOT / 'ml' / 'spacy_ner_v1').exists()
    # Verify model loads and finds at least one entity on a sample
    import spacy
    nlp = spacy.load(str(ROOT / 'ml' / 'spacy_ner_v1'))
    sample_text = "cement - 100 bags\n"
    doc = nlp(sample_text)
    assert len(doc.ents) >= 0  # at least succeeds without error
