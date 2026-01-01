from app.predictor import Predictor


def test_labour_roles_heuristic_and_types():
    p = Predictor()
    req = {
        'materials': [
            'cement: ACC - 50 m3',
            'sand: river sand - 100 m3'
        ],
        'raw_text': 'Concrete works for slab and sand supply'
    }
    out = p.predict(req)
    assert 'labour_roles' in out
    assert isinstance(out['labour_roles'], list)
    # expect at least one role
    assert len(out['labour_roles']) > 0
    assert 'labour_role_types' in out
    assert all(rt in ('skilled', 'unskilled') for rt in out['labour_role_types'].values())
