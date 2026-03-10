/// Contains the hardcoded Gemini prompt used for building-plan structure
/// extraction.  Edit the [prompt] constant to customise the instruction sent
/// to Gemini together with the uploaded images.
class GeminiApiPrompt {
  GeminiApiPrompt._();

  static const String prompt = '''
You are a building-plan measurement extraction engine.

INPUT:
The user uploads images (or PDF pages) of:
- Floor plans (Ground floor, upper floors if any)
- Sections (X-X, Y-Y or similar) — used to extract column heights
- Door/Window schedule tables if present

GOAL:
Read ALL measurable dimensions directly from the plan annotations.
Do NOT calculate or invent values. Record null for anything not clearly shown.

══════════════════════════════════════════════════════════
PART A — WALLS
══════════════════════════════════════════════════════════
1. Identify every distinct wall segment on the ground-floor plan.
   Label them W1, W2, W3 …
2. For EACH wall read from the drawings:
   - height : floor-to-ceiling height (use column height if not annotated).
   - width  : wall thickness (default 0.1150 m / 115 mm half-brick if not annotated).
   - length : wall run length from dimension lines.

══════════════════════════════════════════════════════════
PART B — DOOR SCHEDULE (from the schedule table or plan symbols)
══════════════════════════════════════════════════════════
Label doors D1, D2, D3 …
For each door read:
   - width  : door leaf clear width
   - height : door leaf clear height
   - type   : e.g. "Single", "Double", "Sliding", "Folding"
   - quantity: number of this door type (default 1)

══════════════════════════════════════════════════════════
PART C — WINDOW SCHEDULE (from the schedule table or plan symbols)
══════════════════════════════════════════════════════════
Label windows W1, W2 … (use "WD1" prefix to avoid clash with wall labels).
For each window read:
   - width  : window opening clear width
   - height : window opening clear height
   - type   : e.g. "Fixed", "Casement", "Sliding", "Louvre", "FW"
   - quantity: number of this window type (default 1)

══════════════════════════════════════════════════════════
PART D — FIXED WINDOWS / FW SCHEDULE
══════════════════════════════════════════════════════════
If there is a separate FW (fixed window / fanlight) schedule, extract it as
window entries with type "FW".

STRICT RULES:
- Do NOT calculate any quantities (cement, bricks, etc.).
- Do NOT guess values. Use null for anything not clearly readable.
- Prefer explicit annotation text over visual estimation.
- Consistent units throughout: "m" for metric, "ft" for feet/inches plans.
- Output ONLY valid JSON — no markdown fences, no explanation text.

UNIT NORMALIZATION:
- output.units = "ft" or "m"
- Feet/inches: 5" = 0.4167 ft,  2'-9" = 2.7500 ft
- Round all values to 4 decimal places.

OUTPUT JSON FORMAT (MUST FOLLOW EXACTLY):

{
  "output": {
    "units": "m",
    "scaleText": null,
    "totalWalls": 10,
    "notes": []
  },
  "groundFloor": {
    "walls": {
      "W1": { "height": null, "width": null, "length": null, "notes": [] },
      "W2": { "height": null, "width": null, "length": null, "notes": [] }
    }
  },
  "doors": {
    "D1": { "width": null, "height": null, "type": "Single", "quantity": 1 },
    "D2": { "width": null, "height": null, "type": "Double", "quantity": 1 }
  },
  "windows": {
    "WD1": { "width": null, "height": null, "type": "Casement", "quantity": 1 },
    "WD2": { "width": null, "height": null, "type": "FW", "quantity": 1 }
  },
  "extractionWarnings": []
}
''';

  // ─── Turn 2 (no images, has walling context): Structural Frame columns ───────
  static const String structuralFramePrompt = '''
Now extract ALL COLUMN measurements from the same building plan images you just analysed.

For EACH column (C1, C2, C3 …) read from the drawings:
- height : floor-to-beam-soffit from section / elevation drawings.
- width  : cross-section dimension (X axis).
- length : cross-section dimension (Y axis).

Count every column symbol on the ground-floor plan.
Default to 9×9 grid = 81 columns when the count is not annotated.

STRICT RULES:
- Do NOT calculate any quantities.
- Do NOT guess. Use null for anything not clearly readable.
- Output ONLY valid JSON — no markdown fences, no explanation text.

OUTPUT JSON FORMAT (MUST FOLLOW EXACTLY):

{
  "output": {
    "units": "m",
    "totalColumns": 81,
    "notes": []
  },
  "groundFloor": {
    "columns": {
      "C1": { "height": null, "width": null, "length": null, "notes": [] },
      "C2": { "height": null, "width": null, "length": null, "notes": [] }
    }
  },
  "extractionWarnings": []
}
''';

}
