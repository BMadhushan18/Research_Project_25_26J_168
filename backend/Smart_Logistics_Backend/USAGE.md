# Smart Logistics Backend — Usage & Inputs/Outputs 📋

This document contains the main **inputs**, **outputs**, and **sample commands** for the repository. Use it to run the API shim, train models, and inspect data formats.

---

## Quick overview 🔍
- FastAPI shim: `runtime_shim.py` (app: `app`) — endpoints for demo predictions, authentication, forecasting, document upload, and admin tasks.
- ML scripts: `scripts/train_ml.py`, `scripts/train_updated_model.py` — training RandomForest-based regressors from CSV/BOQ inputs.
- NLP/NER scripts: `scripts/train_spacy_ner.py`, `scripts/train_nlp.py`, `scripts/eval_spacy_ner.py` — work with `data/nlp/annotations.json` to produce `ml/spacy_*` artifacts.
- Document extractor utility: `utils/document_extractor.py` — parse BOQ CSVs and compute features used by the ML code.

---

## API Endpoints (shim) — `runtime_shim.py` 🔧
Run the app with uvicorn (or use `scripts/run_api_checks.py` to exercise endpoints in-process):

```
uvicorn smart_logistics_backend.app:app --reload --host 127.0.0.1 --port 8000
python scripts/run_api_checks.py
```

Endpoints (summary):

- GET `/`  
  Response example:
  ```json
  {"status":"ok","version":"shim","timestamp":"now"}
  ```

- GET `/demo/health`  
  Response: `{"status":"demo ok"}`

- POST `/demo/predict`  
  Request body (JSON):
  ```json
  {"terrain": "urban", "material_tons": 3.5}
  ```
  Response model:
  ```json
  {
    "predicted_fuel_liters": 35.0,
    "predicted_labor_hours": 70.0,
    "total_estimated_cost_LKR": 175000,
    "message": "Prediction successful (shim)"
  }
  ```

- POST `/api/v1/login`  
  Request body:
  ```json
  {"username": "alice", "password": "secret"}
  ```
  Sample response:
  ```json
  {"access_token": "shim-token", "token_type": "bearer", "user_id": "user_1", "username": "alice"}
  ```

- POST `/api/v1/upload-document` (requires header `Authorization: <token>`)  
  - Upload multipart file field `file`; optional `project_name` and `location_type` form fields.
  - Sample response:
  ```json
  {"project_id":"PROJ_SHIM_1","message":"Document processed (shim)","processing_time_seconds":0.1}
  ```
  Example curl for upload:
  ```bash
  curl -X POST "http://127.0.0.1:8000/api/v1/upload-document" -H "Authorization: Bearer shim-token" -F "file=@data/synthetic_boq.csv" -F "project_name=DemoProject"
  ```

- POST `/api/v1/forecast` (requires header `Authorization`)  
  Request body:
  ```json
  {"material_demands": {"cement": 100.0, "sand": 50.0}}
  ```
  Response example:
  ```json
  {"forecasts": {"cement": {"mean":100.0,"std":10.0,"p5":90.0,"p95":110.0},"sand": {"mean":50.0,"std":5.0,"p5":45.0,"p95":55.0}}}
  ```

- Other endpoints: `/api/v1/optimize`, `/api/v1/federated-update`, `/api/v1/projects/{user_id}`, `/api/v1/statistics`, `/admin/reload-config` (admin header `x-admin-token: admin` required for reload).

> ⚠️ Note: The shim uses minimal/deterministic stub logic — production behavior is implemented elsewhere (or by training models in this repo).

---

## ML training scripts & sample inputs 🧠

1) `scripts/train_ml.py`  
   - Input file: `data/ml/synthetic_ml.csv` (CSV with columns: `terrain,distance_km,material_tons,wall_length_m,wall_height_m,fuel_liters,labor_hours,total_cost,vehicle_count`).
   - Run: `python scripts/train_ml.py`
   - Outputs:
     - `ml/prediction_model_v1.pkl` (joblib model)
     - `ml/metrics.json` (metrics per target)
     - `ml/manifest.json`

2) `scripts/train_updated_model.py`  
   - Input BOQ CSV: `data/synthetic_boq.csv` (contains `item,description,quantity,unit,amount,vehicles,` etc.).
   - This script uses `utils.DocumentExtractor()` to compute features and synthesizes training rows for a Random Forest.
   - Run: `python scripts/train_updated_model.py`
   - Outputs:
     - `trained_models/updated_ml_model.pkl`
     - `trained_models/metrics_updated.json`

Sample invocation:
```
python scripts/train_ml.py
python scripts/train_updated_model.py
```

---

## NLP / NER scripts & formats 📝

- Annotations format: `data/nlp/annotations.json`
  Structure: list of `{"doc_id":..., "text": ..., "entities": [[start,end,label], ...]}`. Example:
  ```json
  {
    "doc_id": "doc_0",
    "text": "tiles - 167 ton\ncement - 213 m3\n...",
    "entities": [[0,5,"MATERIAL_NAME"],[17,23,"MATERIAL_NAME"]]
  }
  ```

- `scripts/train_spacy_ner.py` — trains a spaCy model (`ml/spacy_ner_v1`), prints training iterations and dev metrics.
- `scripts/train_nlp.py` — builds a rule-based `ml/spacy_doc_extractor_v1` using an `EntityRuler`.
- `scripts/eval_spacy_ner.py` — evaluates the trained NER on dev set and prints precision / recall / F1 and sample misaligned entities.

Run examples:
```
python scripts/train_spacy_ner.py
python scripts/eval_spacy_ner.py
```

---

## DocumentExtractor utility — `utils/document_extractor.py` 🔎
- Purpose: parse BOQ CSVs into numeric features used by ML.
- Key methods:
  - `parse_boq_csv(csv_path)` -> pandas.DataFrame
  - `compute_features(df)` -> dict with keys: `concrete_volume, steel_quantity, brick_quantity, total_cement_ton, total_sand_ton, site_area, wall_area, total_amount_lkr, vehicles_total, ...`

Example Python usage:
```python
from utils.document_extractor import DocumentExtractor
feats = DocumentExtractor().extract_features_from_csv('data/synthetic_boq.csv')
print(feats['total_amount_lkr'], feats['vehicles_total'])
```

---

## Tests & small checks ✅
- `scripts/run_api_checks.py` runs a FastAPI TestClient in-process and prints responses for `/`, `/demo/health`, `/demo/predict`, and `/api/v1/login`.
- Unit tests available in `tests/` (run with `pytest`).

Run tests:
```
pytest -q
```

---

## Quick tips / troubleshooting 💡
- If an API endpoint requires authorization, use `Authorization: Bearer <token>` header (the shim uses a dummy token returned by `/api/v1/login`).
- The `runtime_shim.py` is intentionally simple — use it to regenerate OpenAPI or run local tests.
- For NER training you need spaCy and compatible packages installed (see `BACKEND_DOCUMENTATION.md` for environment notes).

---

## Where I put this file ✅
`USAGE.md` (this file) at project root: `USAGE.md`

---

If you'd like, I can:
- run `python scripts/run_api_checks.py` and paste the runtime output into this file, or
- expand the file with curl examples for every endpoint, or
- add a short `examples/` folder with ready-to-run scripts.

Tell me which of the above you'd like me to add next.