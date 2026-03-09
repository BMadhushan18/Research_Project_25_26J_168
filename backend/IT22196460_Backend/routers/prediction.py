"""
Prediction Router — exposes three endpoints:

  POST /api/v1/predict/text    → BOQ entered as JSON
  POST /api/v1/predict/file    → BOQ uploaded as PDF or Excel
  GET  /api/v1/models/status   → Check which models are loaded
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional

from models.schemas import (
    BOQTextInput,
    PredictionResponse,
)
from services.feature_extractor import extract_features, get_summary_stats, prepare_model_input
from services.model_service import predict_vehicles, predict_labor, predict_machinery, get_model, get_model_status
from services.cost_service import estimate_costs, generate_waste_recommendations
from services.file_parser import parse_excel, parse_pdf

logger = logging.getLogger(__name__)
router = APIRouter()

SUPPORTED_EXCEL = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
    "application/vnd.ms-excel",  # xls
    "text/csv",
}
SUPPORTED_PDF = {"application/pdf"}


# ─── Helper ──────────────────────────────────────────────────────────

def _run_prediction(
    items: list,
    project_name: str,
    project_type: str,
    duration_days: int,
    site_location: str,
    total_floor_area_sqft: float = 5000.0,
    number_of_floors: int = 1,
    building_complexity_index: float = 5.0,
) -> PredictionResponse:
    if not items:
        raise HTTPException(status_code=422, detail="No valid BOQ items could be extracted.")

    # Feature extraction for fallback heuristics (20-feature vector)
    features = extract_features(items, project_type, duration_days, site_location)
    stats = get_summary_stats(items)

    # Per-item DataFrame for ML models (9-feature schema)
    model_df = prepare_model_input(
        items, project_type, duration_days, site_location,
        total_floor_area_sqft, number_of_floors, building_complexity_index,
    )

    # Model predictions
    vehicles = predict_vehicles(model_df, features)
    labor = predict_labor(model_df, features)
    machinery = predict_machinery(model_df, features)

    # Cost estimate
    cost = estimate_costs(vehicles, labor, machinery, duration_days)

    # Waste recommendations
    recommendations = generate_waste_recommendations(features)

    confidence = _estimate_confidence(stats)
    prediction_sources = {
        "vehicle": "model" if get_model("vehicle") is not None else f"fallback: {get_model_status('vehicle')}",
        "labor": "model" if get_model("labor") is not None else f"fallback: {get_model_status('labor')}",
        "machinery": "model" if get_model("machinery") is not None else f"fallback: {get_model_status('machinery')}",
    }

    return PredictionResponse(
        project_name=project_name,
        total_boq_amount=stats["total_boq_amount"],
        total_quantity=stats["total_quantity"],
        item_count=stats["item_count"],
        vehicles=vehicles,
        labor=labor,
        machinery=machinery,
        cost_estimate=cost,
        waste_recommendations=recommendations,
        prediction_sources=prediction_sources,
        confidence_score=round(confidence, 3),
    )


def _estimate_confidence(stats: dict) -> float:
    """Estimate confidence using item count and data richness from parsed BOQ."""
    item_count = int(stats.get("item_count", 0))
    total_amount = float(stats.get("total_boq_amount", 0))
    total_quantity = float(stats.get("total_quantity", 0))

    base = 0.45
    item_component = min(0.35, item_count * 0.008)
    amount_component = 0.1 if total_amount > 0 else 0.0
    quantity_component = 0.05 if total_quantity > 0 else 0.0
    return max(0.35, min(0.95, base + item_component + amount_component + quantity_component))


# ─── Endpoints ───────────────────────────────────────────────────────

@router.post("/predict/text", response_model=PredictionResponse, summary="Predict from JSON/text BOQ input")
async def predict_from_text(payload: BOQTextInput):
    """
    Accept a structured BOQ as JSON body and return logistics predictions.

    Example body:
    ```json
    {
      "project_name": "New Hospital Block",
      "project_type": "building",
      "project_duration_days": 180,
      "site_location": "Kandy",
      "items": [
        {"description": "Concrete Grade 25 for columns", "unit": "m3", "quantity": 150, "unit_rate": 42000},
        {"description": "Steel reinforcement Y16", "unit": "kg", "quantity": 8500, "unit_rate": 220}
      ]
    }
    ```
    """
    return _run_prediction(
        items=payload.items,
        project_name=payload.project_name or "Unnamed Project",
        project_type=payload.project_type or "building",
        duration_days=payload.project_duration_days or 90,
        site_location=payload.site_location or "Colombo",
        total_floor_area_sqft=payload.total_floor_area_sqft,
        number_of_floors=payload.number_of_floors,
        building_complexity_index=payload.building_complexity_index,
    )


@router.post("/predict/file", response_model=PredictionResponse, summary="Predict from PDF or Excel BOQ upload")
async def predict_from_file(
    file: UploadFile = File(..., description="BOQ file (.xlsx, .xls, or .pdf)"),
    project_name: Optional[str] = Form(default="Unnamed Project"),
    project_type: Optional[str] = Form(default="building"),
    project_duration_days: int = Form(default=90, ge=1, le=3650),
    site_location: Optional[str] = Form(default="Colombo"),
    total_floor_area_sqft: float = Form(default=5000.0, ge=0),
    number_of_floors: int = Form(default=1, ge=1),
    building_complexity_index: float = Form(default=5.0, ge=1, le=10),
):
    """
    Upload a BOQ file (PDF or Excel) to receive logistics predictions.

    Form fields:
    - file: The BOQ file
    - project_name: Name of the project (optional)
    - project_type: building | road | bridge | civil (optional)
    - project_duration_days: Estimated project duration (optional)
    - site_location: City/district in Sri Lanka (optional)
    """
    content_type = file.content_type or ""
    filename = (file.filename or "").lower()

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    items = []

    # Excel
    if content_type in SUPPORTED_EXCEL or filename.endswith((".xlsx", ".xls", ".csv")):
        try:
            items = parse_excel(file_bytes)
        except Exception as e:
            logger.error(f"Excel parsing failed: {e}")
            raise HTTPException(status_code=422, detail=f"Could not parse Excel file: {str(e)}")

    # PDF
    elif content_type in SUPPORTED_PDF or filename.endswith(".pdf"):
        try:
            items = parse_pdf(file_bytes)
        except ImportError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            logger.error(f"PDF parsing failed: {e}")
            raise HTTPException(status_code=422, detail=f"Could not parse PDF file: {str(e)}")

    else:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: '{content_type}'. Please upload .xlsx, .xls, or .pdf."
        )

    return _run_prediction(
        items=items,
        project_name=project_name or "Unnamed Project",
        project_type=project_type or "building",
        duration_days=project_duration_days or 90,
        site_location=site_location or "Colombo",
        total_floor_area_sqft=total_floor_area_sqft,
        number_of_floors=number_of_floors,
        building_complexity_index=building_complexity_index,
    )


@router.get("/models/status", summary="Check model loading status")
async def model_status():
    """Returns which prediction models are currently loaded."""
    return {
        "vehicle_model": "loaded" if get_model("vehicle") is not None else f"fallback (heuristic): {get_model_status('vehicle')}",
        "labor_model": "loaded" if get_model("labor") is not None else f"fallback (heuristic): {get_model_status('labor')}",
        "machinery_model": "loaded" if get_model("machinery") is not None else f"fallback (heuristic): {get_model_status('machinery')}",
    }
