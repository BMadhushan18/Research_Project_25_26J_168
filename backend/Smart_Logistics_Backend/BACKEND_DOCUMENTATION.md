# Smart Logistics AI Model — Backend Documentation (A to Z)

> ✅ Full backend reference, endpoints, inputs/outputs, environment, and test instructions.

---

## Overview

This document describes the Smart Construction Management API ("Smart_Logistics_AI_Model" backend). It covers architecture, environment, authentication, all public API endpoints, request/response schemas, example requests (curl / Python), and how to test locally (Swagger UI, curl, pytest).

Repo location: `backend/Smart_Logistics_Backend/`

API base: the FastAPI app is defined in `smart_logistics_backend/app.py` and served as `app`.

Docs UI: Swagger UI is available at `/api/docs` and ReDoc at `/api/redoc` (when server is running). Example: http://127.0.0.1:8000/api/docs

---

## Quickstart — run locally 🔧

1. Create a virtualenv and install requirements:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend/Smart_Logistics_Backend/requirements.txt
```

2. Run the app with uvicorn:

```bash
uvicorn smart_logistics_backend.app:app --reload --host 127.0.0.1 --port 8000
```

3. Open the Swagger UI: http://127.0.0.1:8000/api/docs

Notes:
- The app uses `uvicorn` when run directly (see `if __name__ == "__main__"` in `app.py`).
- The Swagger docs path is configured as `/api/docs`.

---

## Environment variables & configuration ⚙️

Important environment variables (see `.env` usage in the repo):

- `SECRET_KEY` — JWT secret (default `your-secret-key-change-in-production`).
- `ALGORITHM` — JWT algorithm (default `HS256`).
- `ACCESS_TOKEN_EXPIRE_MINUTES` — token TTL (default `30`).
- `ADMIN_TOKEN` — admin token for `/admin/reload-config` (fallback to `SECRET_KEY` if not set).
- `UPLOAD_DIR` — directory for temporary uploads (default `./temp_uploads`).
- `MAX_FILE_SIZE_MB` — max upload size (default 50).
- MongoDB connection: `MONGO_URI` and `MONGO_DB_NAME` (defaults to `mongodb://localhost:27017/` and `smart_construction_db`).
- `SMART_LOGISTICS_CONFIG` — optional config YAML path for `config.py`.

Configuration loading functions: `backend/Smart_Logistics_Backend/config.py` provides `get_config()` and `reload_config()`.

---

## Authentication 🛡️

- Login: `POST /api/v1/login` accepts `username` and `password` and returns a JWT token (`access_token`).
- Protected endpoints require an `Authorization: Bearer <access_token>` header.
- Admin endpoint `/admin/reload-config` requires header `X-Admin-Token` matching `ADMIN_TOKEN` (or `SECRET_KEY`).

Token creation uses `create_access_token` in `app.py` (JWT with expiration).

---

## Endpoints Reference (A → Z) 📚

Note: The types below map to Pydantic models in `backend/Smart_Logistics_Backend/models.py`. In Swagger UI you can inspect the exact fields and example schemas.

### 1) Health & Root

- GET `/` — Health check
  - Response: `HealthCheckResponse`:
    - `{status, version, timestamp, database_connected, models_loaded}`

- GET `/health` — same as `/`.

### 2) Demo endpoints (no auth required)

- GET `/demo/health`
  - Quick check whether demo model loaded.

- POST `/demo/predict` (tag: `Demo`) — Quick, lightweight predict endpoint for demos and testing.
  - Input: `DemoPredictionInput` (JSON)
    - `terrain` (optional, default `urban`)
    - `distance` (optional)
    - `material_tons` (optional)
    - `labor_type` (optional)
    - `materials` (optional list of MaterialItem {name, qty, unit, ...})
    - `wall` (optional WallSpec {length_m, height_m})
    - `target_days` (optional)
  - Output: `DemoPredictionOutput` (JSON)
    - `predicted_fuel_liters` (float)
    - `predicted_labor_hours` (float)
    - `total_estimated_cost_LKR` (int)
    - `vehicle_allocation` (list of VehicleAllocation)
    - `labor_allocations` (list of LaborAllocation)
    - `manpower_total` (int)
    - `vehicles` (list of VehicleDetail)
    - `cost_breakdown` (CostBreakdown)
  - Example request (curl):

```bash
curl -X POST "http://127.0.0.1:8000/demo/predict" \
  -H "Content-Type: application/json" \
  -d '{"terrain":"urban","material_tons":5}'
```

- Behavior: If `materials` list provided, the demo endpoint uses a helper to compute estimates directly from materials; otherwise builds proxy features and uses `PredictionModel.predict()`.

### 3) Authentication

- POST `/api/v1/login` (tag: `Authentication`)
  - Input: `LoginRequest` — `{username, password}`
  - Output: `TokenResponse` — `{access_token, token_type, user_id, username}`
  - Note: For demo use, the backend will create a user if DB unavailable or user missing.

Example (curl):

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"secret123"}'
```

Response sample:

```json
{
  "access_token": "<JWT>",
  "token_type": "bearer",
  "user_id": "...",
  "username": "alice"
}
```

### 4) Document Upload & Processing (protected)

- POST `/api/v1/upload-document` (tag: `Document Processing`)
  - Auth: Bearer token required.
  - Form fields / multipart:
    - `file`: file upload (XLSX, XLS or PDF)
    - `project_name` (optional, default `Untitled Project`)
    - `location_type` (optional, default `urban`)
    - `weather_condition` (optional, default `normal`)
  - Response: `DocumentUploadResponse` — comprehensive results including:
    - `project_id`, `message`, `extracted_features`, `predictions`, `probabilistic_forecast`, `optimization_results`, `waste_insights`, `explanations`, `processing_time_seconds`.

Example (curl):

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/upload-document" \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@/path/to/boq.xlsx" \
  -F "project_name=Demo Project" \
  -F "location_type=urban"
```

Important validations & behavior:
- Supported extensions: `.xlsx`, `.xls`, `.pdf`.
- File size limited by `MAX_FILE_SIZE_MB`.
- Pipeline steps: extraction (NLP), prediction (ML), bias-correction, probabilistic forecasting, optimization, XAI explanations, persistence to DB.

### 5) Forecasting (protected)

- POST `/api/v1/forecast` (tag: `Forecasting`)
  - Input: `ForecastRequest` — `material_demands` (dict), `uncertainty_factors`, `num_samples`.
  - Output: `ForecastResponse` — `forecasts` (mean/std/p5/p50/p95 per material), `risk_assessment`, `recommendations`.

Example (curl):

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/forecast" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"material_demands":{"cement":1000, "steel":200}}'
```

### 6) Optimization (protected)

- POST `/api/v1/optimize` (tag: `Optimization`)
  - Input: `OptimizationRequest` — `predictions`, `constraints`, `optimization_goals`.
  - Output: `OptimizationResponse` — `optimized_routes`, `material_substitutions`, `waste_reduction_strategies`, `cost_savings`, `time_savings_hours`, `environmental_impact`.

Example: Use predictions from upload or demo as input to optimizer.

### 7) Federated Learning (protected)

- POST `/api/v1/federated-update` (tag: `Federated Learning`)
  - Input: `FederatedUpdateRequest` — `client_id`, `model_parameters`, `num_samples`, `project_metadata`.
  - Output: `FederatedUpdateResponse` — `global_parameters`, `aggregation_round`, `num_clients_participated`, `convergence_metric`.

### 8) Projects & Project Info (protected)

- GET `/api/v1/projects/{user_id}` (tag: `Projects`)
  - Returns `ProjectListResponse` (user_id, list of `ProjectSummary`, `total_projects`).
  - Authorization: Bearer token; the user must be the same as `user_id`.

- GET `/api/v1/project/{project_id}` — Returns full project details (from DB). Authorization: user must be owner.

### 9) Statistics (protected)

- GET `/api/v1/statistics` — returns DB statistics and federated learning stats.

### 10) Admin

- POST `/admin/reload-config` — Reload YAML config into runtime.
  - Header required: `X-Admin-Token: <ADMIN_TOKEN or SECRET_KEY>`.
  - Returns keys loaded from config.

---

## Error handling and status codes ⚠️

- 200 OK — successful responses.
- 400 Bad Request — malformed inputs or file type errors.
- 401 Unauthorized — invalid or missing JWT for protected endpoints.
- 403 Forbidden — insufficient permissions (e.g., wrong user or admin token missing/wrong).
- 413 Payload Too Large — file exceeds `MAX_FILE_SIZE_MB`.
- 500 Internal Server Error — service failure or exceptions.

All errors are returned as JSON with `detail` (FastAPI default) or custom error messages from handlers.

---

## How to test the APIs ✅

1. **Browser / Swagger UI**
   - Start the server, open http://127.0.0.1:8000/api/docs.
   - You can try endpoints interactively. For protected endpoints, first call `/api/v1/login` to get a token, then click "Authorize" in the top-right and add `Bearer <token>`.

2. **curl examples**
   - Login & save token:

```bash
TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/api/v1/login" -H "Content-Type: application/json" -d '{"username":"alice","password":"pass123"}' | jq -r '.access_token')
```

   - Call forecast:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/forecast" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"material_demands":{"cement":500}}'
```

   - Upload file:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/upload-document" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/boq.xlsx" \
  -F "project_name=My Project"
```

3. **Python (requests)**

```python
import requests
base = "http://127.0.0.1:8000"
# login
r = requests.post(base + "/api/v1/login", json={"username":"alice","password":"pw"})
t = r.json()["access_token"]
headers = {"Authorization": f"Bearer {t}"}
# forecast
resp = requests.post(base + "/api/v1/forecast", headers=headers, json={"material_demands":{"cement":100}})
print(resp.json())
```

4. **Automated tests (pytest)**

- Run all tests (project root):

```bash
pytest -q
```

- Run backend tests only:

```bash
pytest backend/Smart_Logistics_Backend/tests -q
```

- Run a single test file:

```bash
pytest backend/Smart_Logistics_Backend/tests/test_demo_endpoints.py -q
```

- Run a single test by name (useful when iterating):

```bash
pytest -k test_demo_health_and_predict -q -s
```

- Notes about test behavior:
  - Some smoke tests (e.g., `test_smoke_inference.py`) will `pytest.skip()` if ML artifacts (`ml/updated_ml_model.pkl`, `ml/updated_feature_cols.pkl`) are missing; ensure model artifacts are available for full coverage.
  - Tests use FastAPI's `TestClient` to exercise endpoints in-process (no external server required).
  - To see logs while running tests, add `-s` to disable capture.

- Running tests with coverage:

```bash
pip install coverage
coverage run -m pytest
coverage html
# open htmlcov/index.html in a browser
```

- Quick smoke run (2025-12-29):

```bash
venv\Scripts\python -m pytest backend/Smart_Logistics_Backend/tests -q
# Result: 29 passed, 3 warnings
```

- CI tips:
  - Run tests in a clean virtualenv.
  - Set `MONGO_URI` to a test database or mock DB to avoid altering production data.

5. **In-code examples & test references**

- The tests folder contains the best examples of expected inputs and outputs. Key tests:
  - `test_demo_endpoints.py` — demo health and predict examples using `TestClient`.
  - `test_api_demo_predict.py` — more API surface checks.
  - `test_smoke_inference.py` — model inference checks (skips if artifacts are missing).

- Use the tests as examples when writing integration tests or new endpoints; they demonstrate how to call `app` directly without a running server.


---

## Internal components & behavior (details) 🧩

- `DocumentExtractor` (utils) — NLP extraction from BOQ/XLSX/PDF to normalized features.
- `PredictionModel` — multi-output model that returns estimates for fuel liters, hours, cost, vehicle counts, and labor allocations.
- `ProbabilisticForecaster` — Monte Carlo / probabilistic forecasts per material.
- `SupplyChainOptimizer` — optimization for routes, substitutions, waste reduction.
- `BehavioralBiasCorrector` — detects and corrects biases in predictions.
- `ExplainabilityEngine` — generates feature importance & local explanations (XAI)
- `FederatedLearningCoordinator` — aggregates updates and returns global parameters

These are initialized (lazy or on startup) in `app.py`.

---

## Security notes 🔒

- The demo login flow is permissive for demo/test purposes. For production, integrate with proper user registration, hashed passwords in DB, and stricter token controls.
- CORS is wide-open (`allow_origins: ["*"]`) in development; lock this down in production.

---

## Troubleshooting & tips 💡

- If you see `Prediction service unavailable` in demo endpoints, check that model files exist and the `ml/` artifacts are present or that `PredictionModel.load_models()` succeeded.
- If the database is unavailable, many endpoints have demo fallbacks but persistence will be disabled. Ensure `MONGO_URI` is correct.
- Check logs in `logs/` for runtime errors.

---

## Appendix: Example Responses

- Login (success):

```json
{
  "access_token": "<JWT>",
  "token_type": "bearer",
  "user_id": "...",
  "username": "alice"
}
```

- Demo predict (success):
```json
{
  "predicted_fuel_liters": 23.4,
  "predicted_labor_hours": 120.5,
  "total_estimated_cost_LKR": 250000,
  "vehicle_allocation": [{"vehicle_type":"Dump Truck","count":2}],
  "labor_allocations": [{"skill_level":"Skilled","category":"Mason","count":4,"hourly_rate":500,"total_hours":120.5,"total_cost":60250}],
  "manpower_total": 6,
  "vehicles": [{"vehicle_type":"Dump Truck","count":2,"fuel_type":"diesel","fuel_per_vehicle_liters":40.0,"fuel_cost_per_vehicle":200.0,"rented":true,"total_vehicle_cost":1200.0}],
  "cost_breakdown": {"labor_cost_total":60000.0,"fuel_cost_total":400.0,"rental_cost_total":800.0,"driver_cost_total":200.0,"other_costs":0.0,"total_cost":61400.0},
  "message":"Prediction successful"
}
```

- Upload-document (success): excerpt
```json
{
  "project_id":"PROJ_20250101010101_TEMP",
  "message":"Document processed successfully",
  "extracted_features": { ... },
  "predictions": { ... },
  "probabilistic_forecast": { ... },
  "optimization_results": { ... },
  "waste_insights": { ... },
  "explanations": { ... },
  "processing_time_seconds": 3.5
}
```

---

## Examples — Detailed Requests & Responses

Below are practical request examples (curl and Python) for common workflows.

### Login (get token)

curl:

```bash
curl -s -X POST "http://127.0.0.1:8000/api/v1/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"secret123"}' | jq .
```

Python:

```python
import requests
r = requests.post("http://127.0.0.1:8000/api/v1/login", json={"username":"alice","password":"secret123"})
print(r.json())
```

Store token for subsequent calls (bash):

```bash
TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/api/v1/login" -H "Content-Type: application/json" -d '{"username":"alice","password":"secret123"}' | jq -r '.access_token')
```

---

### Demo predict (quick test)

Simple curl:

```bash
curl -X POST "http://127.0.0.1:8000/demo/predict" \
  -H "Content-Type: application/json" \
  -d '{"terrain":"urban","material_tons":5}'
```

With materials list (curl):

```bash
curl -X POST "http://127.0.0.1:8000/demo/predict" \
  -H "Content-Type: application/json" \
  -d '{"materials":[{"name":"cement","qty":10,"unit":"bag","unit_size":"50kg"}],"wall":{"length_m":10,"height_m":3}}'
```

Python example:

```python
import requests
r = requests.post("http://127.0.0.1:8000/demo/predict", json={"material_tons":5})
print(r.json())
```

---

### Upload document (multipart upload with auth)

Curl (file upload):

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/upload-document" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/boq.xlsx" \
  -F "project_name=Demo Project" \
  -F "location_type=urban"
```

Python (requests):

```python
import requests
headers = {"Authorization": f"Bearer {TOKEN}"}
files = {"file": open("/path/to/boq.xlsx","rb")}
data = {"project_name":"Demo Project","location_type":"urban"}
r = requests.post("http://127.0.0.1:8000/api/v1/upload-document", headers=headers, files=files, data=data)
print(r.json())
```

Notes: the server validates file extension and size; supported: `.xlsx`, `.xls`, `.pdf`.

---

### Forecast (protected)

Curl:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/forecast" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"material_demands":{"cement":500,"steel":120}}'
```

Python:

```bash
r = requests.post("http://127.0.0.1:8000/api/v1/forecast", headers=headers, json={"material_demands":{"cement":500}})
print(r.json())
```

---

### Optimize (protected)

Use predictions as `predictions` payload. Example curl:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/optimize" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"predictions":{"fuel_liters":100,"estimated_cost":500000},"constraints":{},"optimization_goals":["cost"]}'
```

---

### Federated update (protected)

Curl:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/federated-update" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"client_id":"client_1","model_parameters":{"w": [0.1,0.2]},"num_samples":100}'
```

---

### Projects & stats (protected)

List projects for the logged-in user (example):

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/projects/<user_id>" -H "Authorization: Bearer $TOKEN"
```

Get a project by id:

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/project/<project_id>" -H "Authorization: Bearer $TOKEN"
```

Get statistics:

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/statistics" -H "Authorization: Bearer $TOKEN"
```

---

### Admin reload config (header auth)

```bash
curl -X POST "http://127.0.0.1:8000/admin/reload-config" -H "X-Admin-Token: $ADMIN_TOKEN"
```

---

### Export OpenAPI / Postman import

- Export OpenAPI JSON (server must be running):

```bash
curl -s http://127.0.0.1:8000/openapi.json -o openapi.json
```

- Import `openapi.json` into Postman (File -> Import -> OpenAPI) to generate a collection you can run locally.

- Runtime OpenAPI (generated): `DOCUMENTATION/openapi_runtime.json` — this file was generated from a temporary FastAPI shim because the repository does not include a runnable `smart_logistics_backend` package. To regenerate the runtime OpenAPI from the real app, start the server and re-export `/openapi.json`.

---

## Where to look in repository 🗂️

- API entrypoint: `backend/Smart_Logistics_Backend/app.py`
- Models/schemas: `backend/Smart_Logistics_Backend/models.py`
- Database wrapper: `backend/Smart_Logistics_Backend/database.py`
- Config: `backend/Smart_Logistics_Backend/config.py` and `config.yaml`
- Utility implementations: `backend/Smart_Logistics_Backend/utils/*.py` (DocumentExtractor, PredictionModel, etc.)
- Tests: `backend/Smart_Logistics_Backend/tests/` (examples and smoke tests)
- Prediction model documentation: `backend/Smart_Logistics_Backend/PREDICTION_MODEL.md` (dataset headers, mappings, training summary, operational notes)

---

## Deployment & Environment — production notes 🔧

This section summarises recommended practices for deploying the backend in production and for managing environment variables, secrets, logging, and service lifecycle.

### Recommended environment variables

Create a `.env` (or use your secrets manager) and set at least:

```text
SECRET_KEY=replace-with-secure-random
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ADMIN_TOKEN=replace-with-admin-token
MONGO_URI=mongodb://dbhost:27017/
MONGO_DB_NAME=smart_construction_db
UPLOAD_DIR=/var/smart_logistics/uploads
MAX_FILE_SIZE_MB=50
SMART_LOGISTICS_CONFIG=/etc/smart_logistics/config.yaml
```

Security tips:
- Keep `SECRET_KEY` and `ADMIN_TOKEN` secret (use a secrets manager in cloud environments).
- Restrict CORS in production (do not use `allow_origins: ["*"]`).
- Use TLS/HTTPS via reverse proxy (nginx, Traefik, or managed ingress).

### Running the service

Development / quick run:

```bash
uvicorn smart_logistics_backend.app:app --reload --host 0.0.0.0 --port 8000
```

Production (recommended):
- Run with a process manager (systemd, Windows service) or container orchestration.
- Use multiple workers via Gunicorn + Uvicorn worker for concurrency:

```bash
pip install gunicorn uvicorn
gunicorn -k uvicorn.workers.UvicornWorker "backend/Smart_Logistics_Backend.app:app" -w 4 -b 0.0.0.0:8000
```

### systemd unit (Linux example)

File `/etc/systemd/system/smart-logistics.service`:

```ini
[Unit]
Description=Smart Logistics API
After=network.target

[Service]
User=appuser
Group=appuser
WorkingDirectory=/opt/smart_logistics
EnvironmentFile=/opt/smart_logistics/.env
ExecStart=/opt/smart_logistics/.venv/bin/gunicorn -k uvicorn.workers.UvicornWorker "backend/Smart_Logistics_Backend.app:app" -w 4 -b 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Commands:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now smart-logistics.service
sudo journalctl -u smart-logistics -f
```

### Windows service (brief)

- Use NSSM (Non-sucking Service Manager) or `sc create` to install the service pointing to your Python script/runner.
- Ensure `.env` is loaded for the service environment or configure the registry / service environment variables.

### Docker & docker-compose example

Dockerfile (basic):

```Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install -r backend/Smart_Logistics_Backend/requirements.txt
ENV PYTHONUNBUFFERED=1
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "backend/Smart_Logistics_Backend.app:app", "-w", "4", "-b","0.0.0.0:8000"]
```

docker-compose snippet:

```yaml
version: '3.8'
services:
  app:
    build: .
    env_file:
      - .env
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
    depends_on:
      - mongo
  mongo:
    image: mongo:6
    volumes:
      - mongo-data:/data/db
volumes:
  mongo-data:
```

### Logging & rotation

- The app uses `loguru` and writes logs to `logs/app_{time}.log` (rotation/days configured in `app.py`).
- Ensure `/var/log/smart_logistics` or `./logs` is writable by the service user and set up log rotation / retention as required.

### Backups & DB

- Use MongoDB's backup tools (`mongodump` / managed snapshots) for production backups.
- Prefer running the service with a separate database account and limit privileges.

### Monitoring & health checks

- Expose `/` or `/health` endpoint for liveness checks.
- Configure your orchestrator/load balancer to run periodic health checks against `/health`.

---

## Training & Models 🧠

This repository includes scripts and synthetic data to train baseline ML and NLP models for the Smart Logistics backend.

Files and commands:

- Synthetic data generator: `backend/Smart_Logistics_Backend/scripts/generate_synthetic_data.py` — generates ML CSV and NLP documents + annotations under `data/`.

- Train ML (baseline multi-output regression, scikit-learn):

```bash
python backend/Smart_Logistics_Backend/scripts/generate_synthetic_data.py
python backend/Smart_Logistics_Backend/scripts/train_ml.py
```

Model artifact: `backend/Smart_Logistics_Backend/ml/prediction_model_v1.pkl` — saved with joblib. Metrics are stored in `backend/Smart_Logistics_Backend/ml/metrics.json` and model metadata in `backend/Smart_Logistics_Backend/ml/manifest.json`.

- Train NLP (spaCy EntityRuler extractor + spaCy NER):

```bash
# Rule-based extractor (EntityRuler)
python backend/Smart_Logistics_Backend/scripts/train_nlp.py

# Fix annotation alignment (conservative auto-fix; backup created as `annotations.json.bak`)
python backend/Smart_Logistics_Backend/scripts/fix_annotations.py

# Train a spaCy NER model (uses `data/nlp/annotations.json`)
python backend/Smart_Logistics_Backend/scripts/train_spacy_ner.py

# Quick evaluation
python backend/Smart_Logistics_Backend/scripts/eval_spacy_ner.py
```

Artifacts:

- `backend/Smart_Logistics_Backend/ml/spacy_doc_extractor_v1/` — spaCy rule-based extractor model directory.
- `backend/Smart_Logistics_Backend/ml/spacy_ner_v1/` — spaCy NER model directory (trained from `data/nlp/annotations.json`).

Notes:

- `scripts/fix_annotations.py` performs a conservative, substring-based re-alignment and creates a backup `data/nlp/annotations.json.bak`. Use it before training the NER model when annotations may contain escaped newlines or inconsistent spacing (e.g., `cement - 134 ton`).
- The CI workflow now runs the annotation fix, trains the NER, and evaluates it as part of `CI - Train & Test`.

- Tests (smoke): `tests/test_training.py` — runs generation and training scripts and verifies artifacts exist.

Notes:

- Defaults: synthetic datasets are used in this repo to create a working training pipeline. Replace `data/` with real datasets (CSV and annotations JSON) to train on real data.
- For production training, consider using PyTorch for ML models and transformer-based NLP models (requires GPU for reasonable speed).

---

## Where to look in repository 🗂️

If you want, I can:
- Add a Postman collection with example requests for all endpoints,
- Add cURL examples per endpoint in a separate `examples.md`, or
- Generate an OpenAPI YAML file from the running server and commit it into `DOCUMENTATION/`.

Tell me which of these you'd prefer next.

---

End of documentation file.
