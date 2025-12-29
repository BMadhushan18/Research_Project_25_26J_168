from backend.Smart_Logistics_Backend.utils.document_extractor import DocumentExtractor
from pathlib import Path

def test_extract_features():
    de = DocumentExtractor()
    csv = Path(__file__).resolve().parents[1] / 'data' / 'synthetic_boq.csv'
    feats = de.extract_features_from_csv(csv)
    assert isinstance(feats, dict)
    assert 'concrete_volume' in feats
    assert 'total_cement_ton' in feats
    assert feats['total_amount_lkr'] > 0
    assert feats['vehicles_total'] >= 0
