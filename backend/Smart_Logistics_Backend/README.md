# Smart Logistics Backend

This folder contains a prototype backend for processing a Bill of Quantities (BOQ) and predicting required machinery, transport vehicles, and labour (skilled / unskilled).

Features
- FastAPI inference endpoint `/predict` that accepts `boq_text` and optional `materials` input
- `nlp_parser` to extract materials and quantities from BOQ text (spaCy + heuristics)
- `predictor` with rule-based fallback and optional ML models (trainable with `scripts/train.py`)
- `data/sample_training_data.csv` contains small synthetic examples you can expand

Quickstart
1. Create a virtualenv and install requirements:

   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt

2. (Optional) Install spaCy language model:

   python -m spacy download en_core_web_sm

3. Train ML models (optional):

   python scripts\train.py --data data\sample_training_data.csv --out models

4. Run the API:

Run from the backend folder so the `app` package can be imported (Windows PowerShell):

   Push-Location "g:\Company\New folder\Research\Research_project\Research_Project_25_26J_168\backend\Smart_Logistics_Backend"
   .venv\Scripts\Activate.ps1
   # Start on default port 8000 (may conflict). If 8000 is in use, change to 8001
   & ".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Or start without the reloader (keeps the server process stable):

   & ".venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8001

Example requests

- Predict (JSON):
  - PowerShell:
    Invoke-RestMethod -Uri "http://localhost:8001/predict" -Method Post -Body (@{boq_text='Supply and lay 50 m3 concrete using ACC cement'} | ConvertTo-Json) -ContentType 'application/json'
  - curl:
    curl -s -X POST "http://localhost:8001/predict" -H "Content-Type: application/json" -d '{"boq_text":"Supply and lay 50 m3 concrete using ACC cement"}'
  - Python (httpx):
    python -c "import httpx; r=httpx.post('http://localhost:8001/predict', json={'boq_text':'Supply and lay 50 m3 concrete using ACC cement'}); print(r.text)"

- Train (sync upload):
  - curl:
    curl -X POST "http://localhost:8001/train?background=false" -F "file=@data/training_for_model.csv"
  - Python (httpx):
    python -c "import httpx; f=open('backend/Smart_Logistics_Backend/data/training_for_model.csv','rb'); r=httpx.post('http://localhost:8001/train?background=false', files={'file':('training_for_model.csv', f, 'text/csv')}); print(r.text); f.close()"

- Train (async): POST `/train` (without `background=false`) returns `{ "job_id": "...", "status": "queued" }`. Poll status with GET `/train/{job_id}`.

Running tests

   & ".venv\Scripts\python.exe" -m pytest backend\Smart_Logistics_Backend -q

Generate synthetic data and train locally

# Generate 1,000,000 synthetic rows (chunked, memory efficient)
& ".venv\Scripts\python.exe" scripts\generate_1M_training_data.py --out data\training_data_1M_rows.csv --n 1000000 --chunk-size 10000

# Create derived `training_for_model.csv` from the full dataset (or use `scripts/generate_training_data.py` for smaller sets)
& ".venv\Scripts\python.exe" scripts\generate_training_data.py

# Train (default - RandomForest & RandomForest regressor) on `training_for_model.csv`
& ".venv\Scripts\python.exe" scripts\train.py --data data\training_for_model.csv --out models

# Train on large CSV using sampling (recommended for large datasets)
& ".venv\Scripts\python.exe" scripts\train.py --data data\training_data_1M_rows.csv --subsample 200000 --out models

Notes
- The trainer performs reservoir sampling across the CSV (up to `--subsample` rows) and fits a TF-IDF vectorizer + RandomForest classifiers and regressor on the sampled data. This keeps training bounded and produces a single canonical model set in `models/`:
  - `vectorizer.joblib`, `classifier.joblib`, `mlb_machinery.joblib`, `classifier_roles.joblib`, `mlb_roles.joblib`, `regressor_labour.joblib`.
- If you want to train on the *full* data without sampling, set `--subsample` to a sufficiently large value (memory/time intensive) or use a machine with more resources.

Notes about environment

- Ensure you run commands from the project workspace root or from the `backend/Smart_Logistics_Backend` folder so Python can locate modules and scripts.
- If you see `ModuleNotFoundError: No module named 'app'`, change directory to the backend folder before starting the server or set `PYTHONPATH` accordingly.

Endpoint
- POST /predict
  - body: { "boq_text": "..." }
  - returns: JSON with parsed materials and predicted machinery, vehicles, labour counts

Notes
- The repository contains a rule-based predictor that works without trained model artifacts.
- Add real training data to `data/` and use `scripts/train.py` to build ML models.

Model artifacts
- After running the training script a `models/` directory will contain artifacts:
  - `vectorizer.joblib` - TF-IDF vectorizer for BOQ text
  - `classifier.joblib` - trained multi-label classifier for machinery
  - `mlb_machinery.joblib` - `MultiLabelBinarizer` mapping of machinery labels
  - `regressor_labour.joblib` - regressor that predicts skilled and unskilled counts
Datasets
- `data/training_data_10000_rows.csv` — synthetic wide-schema dataset (10,000 rows). Regenerate with `scripts/generate_training_data.py`.
- `data/training_for_model.csv` — derived dataset formatted for `scripts/train.py` (columns: `boq_text,machinery,vehicles,skilled,unskilled`).

Helper scripts
- `scripts/generate_training_data.py` — creates the synthetic full dataset and the derived training CSV.
- `scripts/inspect_models.py` — utility to quickly inspect saved model artifacts.

Training API
- POST `/train` — Upload a CSV and trigger training. Accepts multipart/form-data with file field `file`.
  - Query param `background` (default true): if true, the job runs asynchronously and the response will include `job_id`.
  - The CSV should have columns: `boq_text,machinery,vehicles,skilled,unskilled` (see `data/training_for_model.csv`).
- GET `/train/{job_id}` — Check job status (`queued`, `running`, `completed`, `failed`).

Example response
```
{
  "parsed": { "materials": [...], "raw_text": "..." },
  "prediction": {
     "machinery": ["Concrete Mixer"],
     "vehicles": ["Bulk Cement Truck"],
     "labour": {"skilled": 2, "unskilled": 4}
  }
}
```

If you'd like, I can now run the training with your real dataset (if you provide it) and commit the resulting model artifacts here. Alternatively I can expand the parser to extract brands and item types more robustly given example BOQs.
