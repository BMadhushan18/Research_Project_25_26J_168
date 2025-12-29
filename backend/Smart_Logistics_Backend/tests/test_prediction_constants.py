from backend.Smart_Logistics_Backend.utils import prediction


def test_sl_adjustments_load_default():
    adj = prediction.load_sl_adjustments_from_config(None)
    assert isinstance(adj, dict)
    assert 'fuel_price_lkr' in adj
    assert 'labor_daily_rates' in adj


def test_apply_sl_adjustments_changes_values():
    sample = {'fuel_liters': 100.0, 'total_cost': 100000.0}
    out = prediction.apply_sl_adjustments(sample, terrain='urban', weather=None)
    assert out['fuel_liters'] != sample['fuel_liters'] or out['total_cost'] != sample['total_cost']
    assert '_applied' in out


def test_fallback_formulas_numeric():
    f = {'concrete_volume': 100.0, 'steel_quantity': 200.0, 'site_area': 1000.0}
    vf = prediction.FALLBACK_FORMULAS['vehicles_needed'](f)
    masons = prediction.FALLBACK_FORMULAS['masons'](f)
    assert isinstance(vf, float) or isinstance(vf, int)
    assert isinstance(masons, float) or isinstance(masons, int)
