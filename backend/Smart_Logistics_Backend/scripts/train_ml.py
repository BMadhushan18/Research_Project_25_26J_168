import pandas as pd
import joblib
import json
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ML_DATA = ROOT / "data" / "ml" / "synthetic_ml.csv"
ML_DIR = ROOT / "ml"
os.makedirs(ML_DIR, exist_ok=True)

def load_data(path):
    df = pd.read_csv(path)
    X = df[["terrain","distance_km","material_tons","wall_length_m","wall_height_h"]] if "wall_length_h" in df.columns else df[["terrain","distance_km","material_tons","wall_length_m","wall_height_m"]]
    y = df[["fuel_liters","labor_hours","total_cost","vehicle_count"]]
    return X,y


def train():
    X,y = load_data(ML_DATA)
    X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2,random_state=0)
    base = RandomForestRegressor(n_estimators=50, random_state=0)
    model = MultiOutputRegressor(base)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    metrics = {}
    for i, col in enumerate(y.columns):
        mae = mean_absolute_error(y_test.iloc[:,i], preds[:,i])
        mse = mean_squared_error(y_test.iloc[:,i], preds[:,i])
        r2 = r2_score(y_test.iloc[:,i], preds[:,i])
        metrics[col] = {"mae": mae, "mse": mse, "r2": r2}
    # Save model and metadata
    joblib.dump(model, ML_DIR / "prediction_model_v1.pkl")
    with open(ML_DIR / "metrics.json","w",encoding="utf-8") as mf:
        json.dump(metrics, mf, indent=2)
    with open(ML_DIR / "manifest.json","w",encoding="utf-8") as mf:
        json.dump({"model":"prediction_model_v1.pkl","framework":"scikit-learn","target_cols":list(y.columns)}, mf, indent=2)
    print("Model trained and saved to ml/prediction_model_v1.pkl")
    print("Metrics:", metrics)

if __name__ == '__main__':
    train()