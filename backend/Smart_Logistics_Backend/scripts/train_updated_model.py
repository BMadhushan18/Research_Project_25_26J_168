import pandas as pd
from pathlib import Path
import joblib
import json
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import sys, pathlib, os
# ensure backend package path is on sys.path
pkg_root = pathlib.Path(__file__).resolve().parents[1]
if str(pkg_root) not in sys.path:
    sys.path.insert(0, str(pkg_root))
from utils.document_extractor import DocumentExtractor

ROOT = Path(__file__).resolve().parents[1]
BOQ = ROOT / 'data' / 'synthetic_boq.csv'
ML_DIR = ROOT / 'ml'
TRAINED = ROOT / 'trained_models'
os.makedirs(ML_DIR, exist_ok=True)
os.makedirs(TRAINED, exist_ok=True)


def build_dataset_from_boq(boq_csv):
    de = DocumentExtractor()
    df = de.parse_boq_csv(boq_csv)
    # compute per-document features (here one file -> one project)
    feats = de.compute_features(df)
    # use target columns if present in BOQ as ground truth
    # For the synthetic BOQ we have vehicle counts and fuel etc in rows; we'll aggregate
    targets = {
        'vehicles_needed': int(df['vehicles'].apply(lambda x: 1 if str(x).strip() else 0).sum()),
        'fuel_liters': float(df['total_fuel_liters'].sum()) if 'total_fuel_liters' in df.columns else 0.0,
        'estimated_hours': float(df['estimated_hours'].sum()) if 'estimated_hours' in df.columns else 0.0,
        'estimated_cost': float(df['estimated_cost_lkr'].sum()) if 'estimated_cost_lkr' in df.columns else 0.0
    }
    # Build a simple DataFrame (single-sample). For training we can amplify using bootstrap/perturbations
    X = pd.DataFrame([{
        'concrete_volume': feats['concrete_volume'],
        'steel_quantity': feats['steel_quantity'],
        'brick_quantity': feats['brick_quantity'],
        'total_cement_ton': feats['total_cement_ton'],
        'total_sand_ton': feats['total_sand_ton'],
        'site_area': feats['site_area'],
        'wall_area': feats['wall_area'],
        'total_amount_lkr': feats['total_amount_lkr'],
        'vehicles_total': feats['vehicles_total']
    }])
    y = pd.DataFrame([targets])
    # expand synthetic dataset by perturbations
    rows = []
    trows = []
    import random
    for i in range(300):
        noise = {k: (1 + random.uniform(-0.1,0.1)) for k in X.columns}
        xr = {k: X.iloc[0][k] * noise[k] for k in X.columns}
        tr = {c: float(y.iloc[0][c]) * (1 + random.uniform(-0.1,0.1)) for c in y.columns}
        rows.append(xr)
        trows.append(tr)
    X_full = pd.DataFrame(rows)
    y_full = pd.DataFrame(trows)
    return X_full, y_full


def train():
    X,y = build_dataset_from_boq(BOQ)
    X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2,random_state=0)
    base = RandomForestRegressor(n_estimators=100, random_state=0)
    model = MultiOutputRegressor(base)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    metrics = {}
    for i, col in enumerate(y.columns):
        mae = mean_absolute_error(y_test.iloc[:,i], preds[:,i])
        mse = mean_squared_error(y_test.iloc[:,i], preds[:,i])
        r2 = r2_score(y_test.iloc[:,i], preds[:,i])
        metrics[col] = {"mae": mae, "mse": mse, "r2": r2}
    joblib.dump(model, TRAINED / "updated_ml_model.pkl")
    with open(TRAINED / "metrics_updated.json","w",encoding="utf-8") as mf:
        json.dump(metrics, mf, indent=2)
    print("Trained updated model and saved to trained_models/updated_ml_model.pkl")
    print(metrics)

if __name__ == '__main__':
    train()