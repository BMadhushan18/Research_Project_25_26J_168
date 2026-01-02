from app.predictor import Predictor
from app.nlp_parser import parse_boq


def test_parse_boq_detects_vehicle_hints():
    parsed = parse_boq('Mobilise two tippers, a pickup truck and boom pump for the night pour')
    assert 'Tipper Truck' in parsed['vehicle_hints']
    assert 'Concrete Pump' in parsed['machinery_hints']


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
    allowed_types = {'skilled', 'unskilled', 'semi-skilled', 'professional', 'support'}
    assert all(rt in allowed_types for rt in out['labour_role_types'].values())


def test_parse_boq_detects_wall_work_type():
    parsed = parse_boq('We need to build a boundary wall with cement blocks.')
    assert parsed['work_type'] == 'wall_construction'


def test_wall_profile_adds_role_details_when_missing_material_roles():
    predictor = Predictor()
    req = {
        'materials': [],
        'raw_text': 'Please build a wall around the site with block masonry',
        'work_type': 'wall_construction',
    }
    out = predictor.predict(req)
    assert 'labour_role_details' in out
    assert any(role['slug'] == 'mason' for role in out['labour_role_details'])
    assert 'mason' in out['labour_roles']


def test_parse_boq_detects_interior_work_type():
    parsed = parse_boq('Complete interior fit out with gypsum ceilings and accent lighting.')
    assert parsed['work_type'] == 'interior_fitout'


def test_interior_profile_exposes_specialist_roles():
    predictor = Predictor()
    req = {
        'materials': [],
        'raw_text': 'Interior fit-out scope covering drywall partitions and timber flooring',
        'work_type': 'interior_fitout',
    }
    out = predictor.predict(req)
    slugs = {role['slug'] for role in out['labour_role_details']}
    assert 'interior_designer' in slugs
    assert 'drywall_carpenter' in slugs
    assert 'drywall_carpenter' in out['labour_roles']


def test_parse_boq_detects_slab_work_type_with_fallback():
    parsed = parse_boq('Night pour planned to cast the roof slab tomorrow.')
    assert parsed['work_type'] == 'slab_concreting'


def test_slab_profile_surfaces_formwork_and_pump_roles():
    predictor = Predictor()
    req = {
        'materials': [],
        'raw_text': 'Need pump crew to pour the slab and install formwork',
        'work_type': 'slab_concreting',
    }
    out = predictor.predict(req)
    slugs = {role['slug'] for role in out['labour_role_details']}
    assert 'formwork_carpenter' in slugs
    assert 'concrete_pump_operator' in slugs
    assert 'formwork_carpenter' in out['labour_roles']


def test_predictor_returns_vehicle_details_and_fuel_plan():
    predictor = Predictor()
    req = {
        'materials': [],
        'raw_text': 'Deck pour with boom pump and transit mixers arriving overnight',
        'work_type': 'slab_concreting',
    }
    out = predictor.predict(req)
    assert out['vehicle_details']
    assert out['machinery_details']
    assert out['fuel_plan']['total_liters'] > 0
    assert out['fuel_plan']['summary_by_fuel_type'].get('Diesel', 0) > 0
    diesel_recs = out['fuel_plan']['fuel_grade_recommendations'].get('Diesel')
    assert diesel_recs
    assert any('Auto Diesel' in entry['grade'] for entry in diesel_recs)
    assert 'Ceylon Petroleum Corporation (CEYPETCO)' in out['fuel_plan']['key_suppliers']
    assert 'Petrol' in out['fuel_plan']['light_fuels']
