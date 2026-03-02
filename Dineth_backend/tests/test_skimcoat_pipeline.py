import pandas as pd
from joblib import load

pipeline = load('models/sri_lanka_skimcoat_pipeline_.joblib')

def test_pipeline_predict_shape():
    assert hasattr(pipeline, 'predict')
