"""
Model Loader — loads the three pre-trained .pkl models once at startup
and exposes predict() helpers for each resource type.
"""

import os
import joblib
import numpy as np
import pandas as pd
import logging
import __main__
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)

# ─── Paths ───────────────────────────────────────────────────────────
MODELS_DIR = Path(__file__).parent.parent / "ml_models"

MODEL_PATHS = {
    "vehicle":  MODELS_DIR / "boq_vehicle_prediction_model.pkl",
    "labor":    MODELS_DIR / "labor_prediction_model.pkl",
    "machinery": MODELS_DIR / "machinery_prediction_model.pkl",
}

# Feature column order expected by each model
VEHICLE_FEATURES = [
    "quantity", "task_description", "unit", "project_type", "site_location",
    "total_floor_area_sqft", "number_of_floors", "building_complexity_index",
    "project_duration_days",
]
LABOR_FEATURES = [
    "quantity", "measurement_type", "project_type", "site_location",
    "total_floor_area_sqft", "number_of_floors", "building_complexity_index",
    "project_duration_days", "task_description",
]
MACHINERY_FEATURES = [
    "task_description", "project_type", "site_location", "unit", "quantity",
    "total_floor_area_sqft", "number_of_floors", "building_complexity_index",
    "project_duration_days",
]

# ─── Global model cache ──────────────────────────────────────────────
_models: dict = {}
_model_status: dict = {}
_model_is_pipeline: dict = {}
MIN_MODEL_FILE_BYTES = 1024


def sparse_to_dense(value):
    """Compatibility shim for pickled sklearn pipelines trained with FunctionTransformer."""
    return value.toarray() if hasattr(value, "toarray") else value


def _load_joblib_model(path: Path):
    """Load a joblib model while providing training-time helper functions expected by the pickle."""
    __main__.sparse_to_dense = sparse_to_dense
    return joblib.load(str(path))


def load_models():
    """Load all three models into memory. Called at app startup."""
    import gc
    # Load smaller models first so they succeed even if the large vehicle model exhausts memory.
    load_order = ["machinery", "labor", "vehicle"]
    for name in load_order:
        path = MODEL_PATHS[name]
        if not path.exists():
            logger.warning(f"Model file not found: {path}. Using fallback estimator.")
            _models[name] = None
            _model_status[name] = "missing"
        else:
            gc.collect()
            try:
                file_size = path.stat().st_size
                if file_size < MIN_MODEL_FILE_BYTES:
                    logger.error(
                        f"❌ {name} model file is invalid or truncated ({file_size} bytes): {path}. "
                        "Replace the .pkl file and restart the app."
                    )
                    _models[name] = None
                    _model_status[name] = f"load_failed: invalid_file ({file_size} bytes)"
                    continue
                model = _load_joblib_model(path)
                _models[name] = model
                _model_is_pipeline[name] = hasattr(model, "named_steps")
                _model_status[name] = "loaded"
                logger.info(f"✅ Loaded model: {name} from {path}")
            except MemoryError:
                size_gb = round(path.stat().st_size / (1024**3), 2)
                logger.error(
                    f"❌ {name} model ({size_gb} GB) needs more RAM than available. "
                    "Close other applications or increase system memory. Falling back to heuristics."
                )
                _models[name] = None
                _model_status[name] = f"load_failed: MemoryError ({size_gb} GB model)"
            except EOFError:
                size_bytes = path.stat().st_size
                logger.error(
                    f"❌ {name} model file is corrupted or incomplete ({size_bytes} bytes): {path}. "
                    "joblib reached EOF while unpickling. Replace the file and restart the app."
                )
                _models[name] = None
                _model_status[name] = f"load_failed: corrupt_file ({size_bytes} bytes)"
            except Exception as e:
                logger.error(f"❌ Failed to load {name} model ({type(e).__name__}): {e!r}")
                _models[name] = None
                _model_status[name] = f"load_failed: {type(e).__name__}"


def get_model(name: str):
    return _models.get(name)


def get_model_status(name: str) -> str:
    return _model_status.get(name, "unknown")


# ─── Per-item prediction helpers ─────────────────────────────────────

def _predict_per_item(model, df: pd.DataFrame, feature_cols: List[str], is_pipeline: bool) -> np.ndarray:
    """
    Run the model on each row of the DataFrame and sum predictions.
    Returns a 1-D array of aggregated outputs.
    """
    model_df = df[feature_cols].copy()

    if is_pipeline:
        # Pipeline handles its own preprocessing (TfidfVectorizer, OneHotEncoder, etc.)
        raw = model.predict(model_df)
    else:
        # Raw MultiOutputRegressor — needs numeric input.
        # Encode string columns to integers via pd.factorize per column,
        # keeping column names so sklearn doesn't warn.
        for col in model_df.columns:
            if model_df[col].dtype == object:
                model_df[col] = pd.factorize(model_df[col])[0]
        raw = model.predict(model_df)

    return np.maximum(raw, 0)


def _aggregate_peak_predictions(raw: np.ndarray, resource_type: str) -> np.ndarray:
    """
    Convert per-item predictions into project-level peak demand.

    Summing all BOQ line predictions overcounts reusable resources because those
    line items are not executed at the same time. Vehicles and machinery use the
    peak single-item demand, while labor uses a small concurrent-workfront sum.
    """
    if raw.ndim == 1:
        return raw

    item_count = raw.shape[0]
    if item_count == 0:
        return np.zeros(raw.shape[1], dtype=np.float64)

    if resource_type == "labor":
        concurrent_workfronts = max(1, min(4, int(np.ceil(np.log2(item_count + 1))) - 1))
        sorted_raw = np.sort(raw, axis=0)
        return sorted_raw[-concurrent_workfronts:].sum(axis=0)

    return raw.max(axis=0)


# ─── Public Prediction Functions ─────────────────────────────────────

def predict_vehicles(model_df: pd.DataFrame, fallback_features: np.ndarray) -> dict:
    model = get_model("vehicle")
    if model is not None:
        try:
            raw = _predict_per_item(model, model_df, VEHICLE_FEATURES, _model_is_pipeline.get("vehicle", False))
            agg = _aggregate_peak_predictions(raw, "vehicle")
            values = [max(0, int(round(v))) for v in agg]
            # Model outputs 8 values: first 5 are vehicle types
            light = values[0] if len(values) > 0 else 0
            medium = values[1] if len(values) > 1 else 0
            heavy = values[2] if len(values) > 2 else 0
            mixer = values[3] if len(values) > 3 else 0
            tipper = values[4] if len(values) > 4 else 0
        except Exception as e:
            logger.error(f"Vehicle prediction error: {e}")
            light, medium, heavy, mixer, tipper = _fallback_vehicles(fallback_features)
    else:
        light, medium, heavy, mixer, tipper = _fallback_vehicles(fallback_features)

    total = light + medium + heavy + mixer + tipper
    trips = max(1, int(total * 2.5))
    return {
        "light_vehicles": light,
        "medium_trucks": medium,
        "heavy_trucks": heavy,
        "concrete_mixers": mixer,
        "tipper_trucks": tipper,
        "total_vehicles": total,
        "estimated_trips_per_day": trips,
    }


def predict_labor(model_df: pd.DataFrame, fallback_features: np.ndarray) -> dict:
    model = get_model("labor")
    if model is not None:
        try:
            raw = _predict_per_item(model, model_df, LABOR_FEATURES, _model_is_pipeline.get("labor", False))
            agg = _aggregate_peak_predictions(raw, "labor")
            values = [max(0, int(round(v))) for v in agg]
            unskilled = values[0] if len(values) > 0 else 0
            semi = values[1] if len(values) > 1 else 0
            skilled = values[2] if len(values) > 2 else 0
            supervisors = values[3] if len(values) > 3 else 0
            engineers = values[4] if len(values) > 4 else 0
        except Exception as e:
            logger.error(f"Labor prediction error: {e}")
            unskilled, semi, skilled, supervisors, engineers = _fallback_labor(fallback_features)
    else:
        unskilled, semi, skilled, supervisors, engineers = _fallback_labor(fallback_features)

    total = unskilled + semi + skilled + supervisors + engineers
    peak = int(total * 1.2)
    return {
        "unskilled_workers": unskilled,
        "semi_skilled_workers": semi,
        "skilled_workers": skilled,
        "supervisors": supervisors,
        "engineers": engineers,
        "total_headcount": total,
        "peak_daily_requirement": peak,
    }


def predict_machinery(model_df: pd.DataFrame, fallback_features: np.ndarray) -> dict:
    model = get_model("machinery")
    if model is not None:
        try:
            raw = _predict_per_item(model, model_df, MACHINERY_FEATURES, _model_is_pipeline.get("machinery", False))
            agg = _aggregate_peak_predictions(raw, "machinery")
            values = [max(0, int(round(v))) for v in agg]
            excavators = values[0] if len(values) > 0 else 0
            bulldozers = values[1] if len(values) > 1 else 0
            cranes = values[2] if len(values) > 2 else 0
            pumps = values[3] if len(values) > 3 else 0
            compactors = values[4] if len(values) > 4 else 0
            scaffolding = values[5] if len(values) > 5 else 0
        except Exception as e:
            logger.error(f"Machinery prediction error: {e}")
            excavators, bulldozers, cranes, pumps, compactors, scaffolding = _fallback_machinery(fallback_features)
    else:
        excavators, bulldozers, cranes, pumps, compactors, scaffolding = _fallback_machinery(fallback_features)

    total = excavators + bulldozers + cranes + pumps + compactors + scaffolding
    hours_per_day = round(total * 6.5, 1)
    return {
        "excavators": excavators,
        "bulldozers": bulldozers,
        "cranes": cranes,
        "concrete_pumps": pumps,
        "compactors": compactors,
        "scaffolding_sets": scaffolding,
        "estimated_machinery_hours_per_day": hours_per_day,
        "total_equipment_units": total,
    }


# ─── Fallback Heuristics (when model file is missing) ────────────────

def _fallback_vehicles(f: np.ndarray):
    weight_tons = f[10]
    amount = f[0]
    scale = max(1, amount / 5_000_000)
    heavy = max(1, int(weight_tons / 200))
    medium = max(1, int(weight_tons / 100))
    light = max(2, int(scale * 2))
    mixer = max(1, int(f[3] / 50))   # concrete qty
    tipper = max(1, int(f[5] / 100)) # earthwork qty
    return light, medium, heavy, mixer, tipper


def _fallback_labor(f: np.ndarray):
    amount = f[0]
    scale = max(1, amount / 1_000_000)
    unskilled = max(5, int(scale * 8))
    semi = max(3, int(scale * 5))
    skilled = max(2, int(scale * 4))
    supervisors = max(1, int(scale * 1.5))
    engineers = max(1, int(scale * 0.5))
    return unskilled, semi, skilled, supervisors, engineers


def _fallback_machinery(f: np.ndarray):
    earthwork = f[5]
    concrete = f[3]
    scale = max(1, f[0] / 5_000_000)
    excavators = max(1, int(earthwork / 500))
    bulldozers = max(0, int(earthwork / 1000))
    cranes = max(0, int(scale * 0.5))
    pumps = max(1, int(concrete / 100))
    compactors = max(0, int(earthwork / 800))
    scaffolding = max(1, int(scale * 2))
    return excavators, bulldozers, cranes, pumps, compactors, scaffolding
