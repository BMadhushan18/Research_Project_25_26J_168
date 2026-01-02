"""Prep script to convert sample BOQ documents into the training CSV format.

Usage:
  python scripts/prepare_boq_training.py --input data/sampleBOQ --out data/training_for_model.csv

It ingests PDFs/Excel/Word/CSV/TXT, extracts text/materials, parses with the
BOQ parser, and labels using the rule/ML predictor to produce pseudo-labels
for machinery, vehicles, and labour counts/roles.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import List

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.file_ingest import ingest_boq_bytes
from app.nlp_parser import parse_boq
from app.predictor import Predictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prepare_boq_training")


def collect_rows(input_dir: Path, predictor: Predictor) -> List[dict]:
    rows: List[dict] = []
    for path in sorted(input_dir.glob("**/*")):
        if not path.is_file() or path.suffix.lower() not in {".pdf", ".xls", ".xlsx", ".csv", ".txt", ".doc", ".docx"}:
            continue
        try:
            data = path.read_bytes()
            ingest = ingest_boq_bytes(data, path.name)
            parsed = parse_boq(ingest.raw_text)
            if ingest.materials:
                parsed["materials"] = ingest.materials
            pred = predictor.predict(parsed)
            # Flatten to training schema expected by scripts/train.py
            rows.append(
                {
                    "boq_text": parsed.get("raw_text", "").replace("\n", " ").strip(),
                    "machinery": ";".join(pred.get("machinery", [])),
                    "vehicles": ";".join(pred.get("vehicles", [])),
                    "skilled": pred.get("labour", {}).get("skilled", 0),
                    "unskilled": pred.get("labour", {}).get("unskilled", 0),
                    "labour_roles": ";".join(pred.get("labour_roles", [])),
                }
            )
            logger.info("Ingested %s -> machinery=%s vehicles=%s", path.name, pred.get("machinery"), pred.get("vehicles"))
        except Exception as exc:  # pragma: no cover - defensive only
            logger.warning("Skipping %s due to error: %s", path.name, exc)
    return rows


def main(args):
    input_dir = Path(args.input).expanduser().resolve()
    if not input_dir.exists():
        raise SystemExit(f"Input dir not found: {input_dir}")
    predictor = Predictor()
    rows = collect_rows(input_dir, predictor)
    if not rows:
        raise SystemExit("No rows collected; ensure sample BOQ files are present.")

    df_new = pd.DataFrame(rows)
    if Path(args.out).exists():
        df_old = pd.read_csv(args.out)
        df = pd.concat([df_old, df_new], ignore_index=True)
        df = df.drop_duplicates(subset=["boq_text"])
    else:
        df = df_new

    df.to_csv(args.out, index=False)
    logger.info("Wrote %d rows to %s", len(df), args.out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/sampleBOQ", help="Folder containing BOQ documents")
    parser.add_argument("--out", default="data/training_for_model.csv", help="Output training CSV path")
    args = parser.parse_args()
    main(args)
