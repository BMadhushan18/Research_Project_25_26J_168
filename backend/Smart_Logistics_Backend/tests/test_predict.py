from app.nlp_parser import parse_boq
from app.predictor import Predictor


def test_parser_basic():
    s = "Supply and lay 50 m3 concrete (cement: 5 ton, sand: 1.5 m3) using ACC brand cement"
    parsed = parse_boq(s)
    assert 'materials' in parsed
    assert len(parsed['materials']) >= 1


def test_predict_rule_based():
    p = Predictor()
    s = "Supply and lay 50 m3 concrete using ACC cement"
    parsed = {'materials': [{'raw': s, 'material': 'cement', 'quantity': 50, 'unit': 'm3', 'brands': ['ACC']}], 'raw_text': s}
    out = p.predict(parsed)
    assert 'machinery' in out
    assert 'vehicles' in out
    assert 'labour' in out
