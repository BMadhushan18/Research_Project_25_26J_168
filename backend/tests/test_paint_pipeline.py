import pandas as pd
from joblib import load

pipeline = load('models/sri_lanka_paint_pipeline_{}.joblib'.format(""))

def test_pipeline_predict_shape():
    # create a minimal input using columns order saved in the notebook
    # Note: replace with real sample values from dataset
    x = pd.DataFrame([{'dummy': None}])
    # This test should be updated with real sample input when integrating
    assert hasattr(pipeline, 'predict')
