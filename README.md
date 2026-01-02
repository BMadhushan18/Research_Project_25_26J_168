# Research Project 25/26J

A Flutter project for the research project with multiple components.

## Project Structure

- `backend/`: Backend code for all components
  - `building_plan_analysis/`
  - `material_estimate/`
  - `wood_identification/`
  - `progress_tracking_and_cost_estimate/`
  - `machine_management/`
- `Smart_Logistics_Frontend/`: Flutter frontend tailored for the FastAPI backend
  - `lib/core`: Theme, shared widgets, models, and the API client
  - `lib/features`: Feature slices (dashboard, prediction, training, health)
  - `lib/navigation`: `AppShell` with a custom navigation bar that fans out the four primary screens

## Getting Started

### Backend (FastAPI)

1. `cd backend/Smart_Logistics_Backend`
2. Install deps: `pip install -r requirements.txt`
3. Run tests (optional but recommended): `pytest`
4. Launch the API: `uvicorn app.main:app --host 0.0.0.0 --port 8001`

The backend exposes `/predict`, `/train`, `/train/{job_id}`, and `/db/health`. MongoDB is optional; predictions/train jobs will fall back to in-memory tracking when the database is offline.

### Frontend (Flutter)

1. `cd Smart_Logistics_Frontend`
2. Fetch packages: `flutter pub get`
3. Run the UI: `flutter run -d <device>`

The Flutter shell boots into a "Smart Logistics" dashboard. Open the **Command** tab (first tab) to confirm or edit the backend URL. Defaults:

- Android emulator → `http://10.0.2.2:8001`
- iOS simulator / desktop / web → `http://localhost:8001`

Use the remaining tabs to:

- **Predict** – paste BOQ text, add manual materials, and visualize machinery, vehicles, and labour demand. Results note whether the ML or the rule engine was used.
- **Train** – pick a CSV (`boq_text, machinery, vehicles, skilled, unskilled, labour_roles`) and submit synchronous or background training jobs.
- **Health** – ping `/db/health`, view the resolved base URL, and follow the built-in incident checklist.

All requests flow through `lib/core/services/api_client.dart`, which stores the chosen base URL in `SharedPreferences`.

## Speech-to-Text (Voice button)

The home screen contains a "Voice" button. When pressed, it will start listening using the platform's speech recognition and display the recognized text in the square container on the home screen in real-time.

Platform permissions
- Android: The app requests RECORD_AUDIO permission. Ensure the permission is allowed in Settings or runtime permission dialog when prompted.
- iOS: Info.plist contains NSMicrophoneUsageDescription. You will be asked for microphone access on first use.

To try it manually, run the app on a physical device or Android/iOS emulator and press the "Voice" button; speak into the microphone and you should see the text update in the square.

---

**Note:** The following project folders were moved into `backend/Smart_Logistics_Backend/` to keep backend assets together: `data/`, `DOCUMENTATION/`, `ml/`, `notebooks/`, `scripts/`, and `tests/`.

If you have CI/workflows or scripts that reference their old locations, update paths to `backend/Smart_Logistics_Backend/` accordingly.

---

## Backend documentation & API examples 🔧

The backend documentation and API examples are available in the repository:

- `backend/Smart_Logistics_Backend/BACKEND_DOCUMENTATION.md` — Full A→Z backend documentation, endpoints, environment, and testing instructions.
- `backend/Smart_Logistics_Backend/PREDICTION_MODEL.md` — Detailed prediction model spec, dataset headers, mappings and training results.
- `backend/Smart_Logistics_Backend/EXAMPLES.md` — Per-endpoint cURL and Python snippets for quick testing.
- `backend/Smart_Logistics_Backend/postman_collection.json` — Postman collection you can import into Postman.
- `backend/Smart_Logistics_Backend/DOCUMENTATION/openapi.json` — OpenAPI (v3) specification generated from the documentation.

Start the backend locally and view Swagger UI at `http://127.0.0.1:8000/api/docs`.