from app.predictor import Predictor


def test_predict_with_materials_override():
    p = Predictor()
    req = {
        'materials': [
            'cement: ACC - 5 ton',
            'sand: river sand - 10 m3',
            'aggregate: 20 mm - 15 m3'
        ],
        'raw_text': 'Supply and lay concrete for ground floor slab.'
    }
    out = p.predict(req)
    # Expect machinery/vehicles and labour to be non-empty / positive
    assert isinstance(out['machinery'], list)
    assert isinstance(out['vehicles'], list)
    assert isinstance(out['labour'], dict)
    assert (len(out['machinery']) > 0) or (len(out['vehicles']) > 0) or (out['labour']['skilled'] > 0) or (out['labour']['unskilled'] > 0)
