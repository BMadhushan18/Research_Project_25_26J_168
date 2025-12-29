# Example integration snippet showing how to load the model and predict
from backend.Smart_Logistics_Backend.utils.prediction import load_model, predict_from_features, predict_from_boq_csv

# Load model (from ml/prediction_model_v1.pkl)
load_model()

# Predict from explicit features
features = {"terrain": 0, "distance_km": 12.0, "material_tons": 10.0, "wall_length_m": 20.0, "wall_height_m": 3.0}
print(predict_from_features(features))

# Or predict from a BOQ CSV
print(predict_from_boq_csv('backend/Smart_Logistics_Backend/data/synthetic_boq.csv'))
