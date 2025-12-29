# Research Project 25/26J

A Flutter project for the research project with multiple components.

## Project Structure

- `backend/`: Backend code for all components
  - `building_plan_analysis/`
  - `material_estimate/`
  - `wood_identification/`
  - `progress_tracking_and_cost_estimate/`
  - `machine_management/`
- `frontend/`: Flutter frontend
  - `lib/`: Main library
    - `auth/`: Authentication related code
    - `utils/`: Utility functions
    - `widgets/`: Common widgets
    - `building_plan_analysis/`: Building plan analysis component
    - `material_estimate/`: Material estimate component (moved from old project)
    - `wood_identification/`: Wood identification component
    - `progress_tracking_and_cost_estimate/`: Progress tracking and cost estimate component
    - `machine_management/`: Machine management component

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Lab: Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://docs.flutter.dev/cookbook)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.

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