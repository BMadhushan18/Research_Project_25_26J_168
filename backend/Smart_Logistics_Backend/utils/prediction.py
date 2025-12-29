import joblib
from pathlib import Path
import pandas as pd

"""# Updated Prediction Model & Calculation Documentation (December 2025)

## Project & Model Overview
The Intelligent Multi-Modal Resource Logistics Optimizer predicts vehicles, labor (by skill level: Unskilled, Semi-skilled, Skilled, Professional), drivers, fuel, hours, and cost for Sri Lankan construction projects. It uses NLP to parse BOQs, ML/DL models trained on synthetic + BOQ data, and a material-driven pipeline that maps materials→tasks→vehicles/labor→cost. Sri Lanka adjustments (monsoon, urban congestion) and fallback heuristics are included below.

(See repository PREDICTION_MODEL.md for full, copy-pasted spec.)

## Key Constants & Mappings
- TASK_VEHICLE_MAP: maps tasks to candidate vehicles
- VEHICLE_DETAILS: fuel/rental/driver cost table
- LABOR_SKILL_MAP: skills required per task
- SL_ADJUSTMENTS: Sri Lanka-specific multipliers and rates
- FALLBACK_FORMULAS: conservative heuristics when model missing
"""

ROOT = Path(__file__).resolve().parents[1]
ML_DIR = ROOT / "ml"
MODEL_PATH = ML_DIR / "prediction_model_v1.pkl"

# Core mappings and constants (implemented from spec)
TASK_VEHICLE_MAP = {
    "Excavation & Earthwork": ["Excavator", "Bulldozer", "Dump Truck"],
    "Concrete Works": ["Concrete Mixer Truck", "Concrete Pump"],
    "Masonry & Blockwork": ["Tipper Truck", "Loader"],
    "Formwork & Shuttering": ["Flatbed Truck"],
    "Steel Reinforcement": ["Flatbed Truck"],
    "Roofing": ["Flatbed Truck", "Mobile Crane"],
    "Tiling & Flooring": ["Tipper Truck"],
    "Plastering & Painting": ["Pickup Truck"],
    "Plumbing & Electrical": ["Pickup Truck"],
    "Metal Work": ["Pickup Truck"],
    "Waste Removal": ["Dump Truck"]
}

VEHICLE_DETAILS = {
    "Excavator (Mid-Size)": {"fuel_per_hour": 12, "rental_daily": 30000, "driver_daily": 6000},
    "Dump Truck (10-Ton)": {"fuel_per_hour": 25, "rental_daily": 20000, "driver_daily": 5500},
    "Tipper Truck (6m³)": {"fuel_per_hour": 20, "rental_daily": 18000, "driver_daily": 5000},
    "Flatbed Truck": {"fuel_per_hour": 18, "rental_daily": 22000, "driver_daily": 6000},
    "Concrete Mixer Truck": {"fuel_per_hour": 30, "rental_daily": 35000, "driver_daily": 6500},
    "Mobile Crane": {"fuel_per_hour": 15, "rental_daily": 80000, "driver_daily": 9000}
}

LABOR_SKILL_MAP = {
    "Excavation": ["Unskilled", "Skilled (Operator)"],
    "Concrete": ["Skilled (Bar Bender)", "Semi-skilled", "Unskilled"],
    "Masonry": ["Skilled (Mason)", "Semi-skilled", "Unskilled"],
    "Plastering/Tiling": ["Skilled (Tiler/Mason)", "Semi-skilled"],
    "Painting": ["Skilled (Painter)", "Semi-skilled"],
    "Plumbing/Electrical": ["Skilled (Plumber/Electrician)", "Semi-skilled"],
    "Metal Work": ["Skilled (Welder)"],
    "Supervision": ["Professional (Foreman)"]
}

SL_ADJUSTMENTS = {
    "urban": {"time_multiplier": 1.15, "cost_multiplier": 1.10},
    "rural": {"time_multiplier": 1.0, "cost_multiplier": 0.95},
    "monsoon": {"time_multiplier": 1.30, "cost_multiplier": 1.20},
    "dry": {"time_multiplier": 1.0, "cost_multiplier": 1.0},
    "fuel_price_lkr": 350,
    "labor_daily_rates": {
        "Unskilled": 4000,
        "Semi-skilled": 5500,
        "Skilled": 7000,
        "Professional": 15000
    },
    "driver_daily_rate": 5500
}

FALLBACK_FORMULAS = {
    "vehicles_needed": lambda f: (f.get("concrete_volume", 0) / 50) + (f.get("steel_quantity", 0) / 500) + 2,
    "masons": lambda f: (f.get("concrete_volume", 0) / 20) + (f.get("site_area", 0) / 100) + 3,
    "laborers": lambda f: (f.get("concrete_volume", 0) / 10) + (f.get("site_area", 0) / 50) + 5,
    "fuel_liters": lambda f: (f.get("concrete_volume", 0) * 5) + (f.get("site_area", 0) * 0.5) + 100,
    "estimated_hours": lambda f: (f.get("concrete_volume", 0) * 10) + (f.get("site_area", 0) * 2) + 200,
    "estimated_cost": lambda f: (f.get("concrete_volume", 0) * 15000) + (f.get("steel_quantity", 0) * 200) + (f.get("site_area", 0) * 1000)
}

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


def load_sl_adjustments_from_config(config_path: str = None):
    """Load SL adjustments and mappings from a YAML config file.
    Falls back to embedded SL_ADJUSTMENTS if PyYAML is not available or file missing.
    """
    if config_path is None:
        cfg = ROOT / 'config.yaml'
        if not cfg.exists():
            cfg = ROOT / 'config_example.yaml'
        config_path = str(cfg)
    try:
        import yaml
    except Exception:
        # PyYAML not available; return built-in adjustments
        return SL_ADJUSTMENTS
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        # prefer structured SL_ADJUSTMENTS if present
        return data.get('SL_ADJUSTMENTS', data)
    except Exception:
        return SL_ADJUSTMENTS


def apply_sl_adjustments(preds: dict, terrain: str = 'urban', weather: str = None, adjustments: dict = None):
    """Apply Sri Lanka adjustment multipliers to model predictions.
    Modifies fuel_liters and total_cost using multipliers from adjustments.
    """
    adj = adjustments or SL_ADJUSTMENTS
    terrain_adj = adj.get(terrain, {})
    time_mult = terrain_adj.get('time_multiplier', terrain_adj.get('time_mult', 1.0))
    cost_mult = terrain_adj.get('cost_multiplier', terrain_adj.get('cost_mult', 1.0))
    # apply monsoon if specified
    if weather == 'monsoon' or adj.get('monsoon'):
        time_mult *= adj.get('monsoon', {}).get('time_multiplier', adj.get('monsoon', {}).get('time_mult', 1.3))
        cost_mult *= adj.get('monsoon', {}).get('cost_multiplier', adj.get('monsoon', {}).get('cost_mult', 1.2))
    # adjust fuel and cost
    out = preds.copy()
    if 'fuel_liters' in out:
        out['fuel_liters'] = out['fuel_liters'] * time_mult
    if 'total_cost' in out:
        out['total_cost'] = out['total_cost'] * cost_mult
    # attach applied multipliers for transparency
    out['_applied'] = {'time_mult': time_mult, 'cost_mult': cost_mult}
    return out


def predict_from_features(features: dict, config_path: str = None):
    """Accept a dict of features and return model predictions (dict).
    Expected features: terrain, distance_km, material_tons, wall_length_m, wall_height_m
    This function will apply Sri Lanka adjustments when config is available.
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
    raw = dict(zip(cols, preds[0]))
    # load adjustments and apply
    adjustments = load_sl_adjustments_from_config(config_path)
    terrain = features.get('terrain', 'urban')
    weather = features.get('weather')
    adjusted = apply_sl_adjustments(raw, terrain=terrain, weather=weather, adjustments=adjustments)
    return adjusted

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
