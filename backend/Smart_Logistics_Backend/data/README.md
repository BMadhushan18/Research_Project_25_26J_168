# Dataset files

This folder contains generated and original datasets used for training and experimentation.

Files
- `training_data_10000_rows.csv` — Generated synthetic wide-schema dataset (10,000 rows). Use `scripts/generate_training_data.py` to regenerate.
- `training_for_model.csv` — Derived dataset formatted for the training script (`scripts/train.py`), columns: `boq_text,machinery,vehicles,skilled,unskilled`.

Regeneration
- Run `python scripts/generate_training_data.py` from the project root (or from this folder with the activated venv) to recreate both CSVs.

Notes
- The synthetic dataset is for prototyping; replace it with real annotated BOQs to get production-grade models.
