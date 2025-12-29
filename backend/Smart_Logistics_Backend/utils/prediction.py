import joblib
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ML_DIR = ROOT / "ml"
MODEL_PATH = ML_DIR / "prediction_model_v1.pkl"

class ModelNotLoaded(Exception):
    pass

_model = None


def load_model(path: str = None):
    global _model
    p = MODEL_PATH if path is None else Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Model not found: {p}")
    _model = joblib.load(p)
    return _model


def predict_from_features(features: dict):
    """Accept a dict of features and return model predictions (dict).
    Expected features: terrain, distance_km, material_tons, wall_length_m, wall_height_m
    """
    if _model is None:
        raise ModelNotLoaded("Model not loaded. Call load_model() first.")
    df = pd.DataFrame([{
        "terrain": features.get("terrain", 0),
        "distance_km": features.get("distance_km", 0.0),
        "material_tons": features.get("material_tons", 0.0),
        "wall_length_m": features.get("wall_length_m", 0.0),
        "wall_height_m": features.get("wall_height_m", 0.0)
    }])
    preds = _model.predict(df)
    cols = ["fuel_liters","labor_hours","total_cost","vehicle_count"]
    return dict(zip(cols, preds[0]))


def predict_from_boq_csv(csv_path: str):
    """Simple helper to aggregate BOQ CSV into model features and predict.
    This is a basic example - for production you should use the full extraction pipeline.
    """
    p = Path(csv_path)
    if not p.exists():
        raise FileNotFoundError(f"BOQ file not found: {p}")
    df = pd.read_csv(p)
    # naive aggregation: sum quantities and approximate material_tons
    if 'quantity' in df.columns:
        total_qty = df['quantity'].astype(float).sum()
    else:
        total_qty = 0.0
    # approximate material_tons (assuming qty is in bags where 20 bags ~ 1 ton)
    material_tons = total_qty / 20.0
    features = {"terrain": 0, "distance_km": 10.0, "material_tons": material_tons, "wall_length_m": 0.0, "wall_height_m": 0.0}
    return predict_from_features(features)
