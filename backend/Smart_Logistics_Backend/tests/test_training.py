import subprocess
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_generate_data_and_train(tmp_path):
    # Run data generator (use absolute script paths to avoid cwd issues)
    gen_script = str(ROOT / "scripts" / "generate_synthetic_data.py")
    r = subprocess.run(["python", gen_script])
    assert r.returncode == 0
    # Check files
    assert (ROOT / "data" / "ml" / "synthetic_ml.csv").exists()
    assert (ROOT / "data" / "nlp" / "annotations.json").exists()
    # Train ML
    train_ml_script = str(ROOT / "scripts" / "train_ml.py")
    r2 = subprocess.run(["python", train_ml_script])
    assert r2.returncode == 0
    assert (ROOT / "ml" / "prediction_model_v1.pkl").exists()
    assert (ROOT / "ml" / "metrics.json").exists()
    # Train NLP
    train_nlp_script = str(ROOT / "scripts" / "train_nlp.py")
    r3 = subprocess.run(["python", train_nlp_script])
    assert r3.returncode == 0
    assert (ROOT / "ml" / "spacy_doc_extractor_v1").exists()
    # Run updated training pipeline
    train_updated_script = str(ROOT / "scripts" / "train_updated_model.py")
    r4 = subprocess.run(["python", train_updated_script])
    assert r4.returncode == 0
    assert (ROOT / "trained_models" / "updated_ml_model.pkl").exists()
