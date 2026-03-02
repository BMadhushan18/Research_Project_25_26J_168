# Copilot instructions — My Flutter + FastAPI project

Quick actionable guidance for AI agents who will edit or extend this repo.

## Big picture
- **Two-tier app:** Flutter frontend at `frontend/my_flutter_app` and FastAPI backend at `backend`. The backend currently serves tabular ML predictions (wood/paint/skimcoat); image endpoints are not yet implemented.
- **Where ML lives:** Data and model code are under `backend/` (`wood_predi.py`, `paint_predi.py`, `skimCoat_predi.py`). Frontend calls backend HTTP endpoints (see `lib/pages/wood_material_page.dart`).

## Local dev & run commands
- Backend (dev):
  - cd `backend`
  - python -m venv .venv && .\.venv\Scripts\activate
  - pip install -r requirements.txt
  - run: `uvicorn app:app --reload --host 0.0.0.0 --port 8000`
- Frontend (dev):
  - cd `frontend/my_flutter_app`
  - `flutter pub get`
  - `flutter run -d <device>`

## Key project-specific patterns & conventions
- Pages live in `lib/pages/` and are added to `HomePage` via `CategoryCard` entries (`lib/widgets/category_card.dart`). Follow that pattern when adding new features.
- HTTP client in Flutter uses `package:http` directly and posts JSON or multipart form data. Example call: `http.post(Uri.parse('http://172.28.5.108:8000/predict/wood'), ...)` in `lib/pages/wood_material_page.dart`. Replace hardcoded host with a config value when possible.
- UI pattern: straightforward `StatefulWidget` + `setState` updates; there is no global state library yet (Provider/Bloc). For small features keep using `setState` to match style; consider adding Provider if state grows.

## Integration points & recommended API shapes
- Existing endpoints:
  - POST `/predict/wood` — accepts JSON {price, size, location, building_type} and returns `{"wood_species": "...", "wood_grade": "..."}` (see `app.py`).
- Suggested new endpoints for CV features (backend change required):
  - POST `/predict/wood_image` (multipart file: `image`) -> `{ "species": "Oak", "confidence": 0.92 }`
  - POST `/inspect/defects` (multipart file: `image`) -> `{ "defects": [{"label":"crack","score":0.95,"severity":"high", "bbox": [x,y,w,h]}] }`
- Frontend service stub: `lib/services/ml_api.dart` (added) shows how to send multipart requests and client-side fallback heuristics. Keep response shapes consistent with these examples.

## Frontend UI guidance & examples
- Add new pages under `lib/pages/` and a small `Widget` under `lib/widgets/` (see `result_card.dart` added). Example pattern:
  - Create `MyNewPage` under `lib/pages/`
  - Import it in `lib/pages/home_page.dart`
  - Add a `CategoryCard` entry that pushes it with `Navigator.push(MaterialPageRoute(...))`.
- For camera/image workflows prefer `image_picker` for uploads and `camera` for real-time streams. `pubspec.yaml` was updated to include `image_picker`.

## Model & inference notes
- Current numeric models are Python scikit-learn artifacts called from `backend` scripts. For image models add a subpackage `backend/models/` and expose lightweight inference endpoints. Prefer ONNX/TorchScript/TFLite for performance if moving to mobile or edge.
- For real-time detection consider WebSocket or streaming approaches; for prototyping simple per-frame POSTs are acceptable but will be bandwidth-heavy.

## Debugging and testing tips
- Test backend endpoints with curl or httpie. Example:
  - curl -F "image=@/path/to/img.jpg" http://localhost:8000/inspect/defects
- Keep the backend host configurable: avoid hardcoding `172.28.5.108:8000` in frontend files; instead use a single `Config` class or `.env` file.

## Files worth checking for context
- `backend/app.py` (FastAPI routes)
- `backend/wood_predi.py` (existing ML logic)
- `backend/*_dataset*.csv` (training data)
- `frontend/my_flutter_app/lib/pages/wood_material_page.dart` (example HTTP usage)
- `frontend/my_flutter_app/lib/widgets/category_card.dart` (UI pattern)
- `frontend/my_flutter_app/lib/services/ml_api.dart` (client stub for image endpoints)

## Small rules for edits
- Keep new UI pages simple and match existing Material styling (orange primary color). Use `CategoryCard` for home entries.
- Return JSON structures with stable keys (e.g., `species`, `confidence`, `defects`) so the Flutter client can parse predictably.
- When adding native plugins (`camera`, etc.) update `pubspec.yaml` and run `flutter pub get` and add platform setup notes in the README.

---
If you'd like, I can now create a minimal backend endpoint for `/inspect/defects` (FastAPI + placeholder response) and hook up the Flutter pages to a local dev backend so you can test end-to-end. Feedback on the instructions file is welcome—tell me which sections you want expanded or examples you'd like added.