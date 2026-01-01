import os
import json
import logging
import joblib
from typing import Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODELS_DIR = os.path.join(DATA_DIR, '..', 'models')

# Load rules from config file
def _load_rules():
    """Load material rules from JSON config; fallback to empty dict if missing."""
    rules_path = os.path.join(os.path.dirname(__file__), 'rules.json')
    try:
        with open(rules_path, 'r') as f:
            config = json.load(f)
            rules = config.get('materials', {})
            logger.info(f'Loaded {len(rules)} materials from rules.json')
            return rules
    except FileNotFoundError:
        logger.warning(f'rules.json not found at {rules_path}; using empty rules')
        return {}
    except json.JSONDecodeError as e:
        logger.error(f'Failed to parse rules.json: {e}')
        return {}

RULES = _load_rules()

class Predictor:
    def __init__(self):
        self.models = {}
        self.model_loaded = False
        self._try_load_models()

    def _try_load_models(self):
        """Attempt to load canonical model artifacts if present; log errors."""
        try:
            self.models['vectorizer'] = joblib.load(os.path.join(MODELS_DIR, 'vectorizer.joblib'))
            self.models['clf'] = joblib.load(os.path.join(MODELS_DIR, 'classifier.joblib'))
            self.models['mlb_mach'] = joblib.load(os.path.join(MODELS_DIR, 'mlb_machinery.joblib'))
            # Labour regressor (multi-output)
            try:
                self.models['reg'] = joblib.load(os.path.join(MODELS_DIR, 'regressor_labour.joblib'))
            except (FileNotFoundError, Exception) as e:
                logger.warning(f'Labour regressor not found: {e}')
                self.models['reg'] = None
            # Labour roles classifier and binarizer (optional)
            try:
                self.models['clf_roles'] = joblib.load(os.path.join(MODELS_DIR, 'classifier_roles.joblib'))
                self.models['mlb_roles'] = joblib.load(os.path.join(MODELS_DIR, 'mlb_roles.joblib'))
            except (FileNotFoundError, Exception) as e:
                logger.warning(f'Labour roles classifier not found: {e}')
                self.models['clf_roles'] = None
                self.models['mlb_roles'] = None
            self.model_loaded = True
            logger.info('Successfully loaded all ML models')
        except (FileNotFoundError, Exception) as e:
            # No ML models available; we'll use rule-based fallback
            logger.warning(f'ML models not available; using rule-based predictions: {e}')
            self.models = {}
            self.model_loaded = False

    def _parse_material_string(self, text: str):
        """Parse strings like 'cement: ACC - 5 ton' or 'sand 10 m3' to extract name, quantity and unit."""
        import re
        s = str(text)
        # Try patterns: 'name: brand - qty unit' or 'name qty unit' or 'qty unit name'
        qty_unit_re = re.compile(r"(?P<qty>\d+(?:[\.,]\d+)?)\s*(?P<unit>m3|m|kg|ton|tons|tonne|tonnes|pcs|pieces|bag|tonne|ltr|m2)?", re.I)
        name = None
        qty = None
        unit = None
        # attempt to split by ':' first
        if ':' in s:
            name_part, rest = s.split(':', 1)
            name = name_part.strip().lower()
            # find qty in rest
            m = qty_unit_re.search(rest)
            if m:
                qty = float(m.group('qty').replace(',', '.'))
                unit = m.group('unit')
        else:
            # fallback: search qty and take surrounding tokens as name
            m = qty_unit_re.search(s)
            if m:
                qty = float(m.group('qty').replace(',', '.'))
                unit = m.group('unit')
                # attempt to get name from start up to qty
                idx = m.start()
                name = s[:idx].strip().lower()
                if not name:
                    # try after qty
                    name = s[m.end():].strip().lower()
            else:
                name = s.strip().lower()
        # normalize name (take first token)
        if name:
            name = name.split()[0]
        return name, qty, unit

    def predict(self, parsed_boq: Dict[str, Any]) -> Dict[str, Any]:
        materials = parsed_boq.get('materials', [])
        aggregated = {
            'machinery': set(),
            'vehicles': set(),
            'labour': {'skilled': 0, 'unskilled': 0}
        }

        material_texts = []
        heuristic_roles = set()
        for m in materials:
            # support dicts (from NLP) and string overrides provided by user
            if isinstance(m, dict):
                name = (m.get('material') or m.get('raw') or '').lower()
                qty = m.get('quantity')
                unit = m.get('unit')
            else:
                name, qty, unit = self._parse_material_string(str(m))
            material_texts.append(str(m))

            # Rule-based lookup
            for kw, out in RULES.items():
                if name and kw in name:
                    aggregated['machinery'].update(out['machinery'])
                    aggregated['vehicles'].update(out['vehicles'])
                    aggregated['labour']['skilled'] += out['labour']['skilled']
                    aggregated['labour']['unskilled'] += out['labour']['unskilled']

            # Quantity-aware heuristics
            try:
                if name and (name in ('concrete', 'cement') or 'concrete' in str(m).lower()):
                    q = qty or 0
                    if unit and unit.lower() in ('m3', 'm'):
                        # mixers per 50 m3
                        import math
                        mixers = max(1, math.ceil(q / 50))
                        aggregated['machinery'].add('Concrete Mixer')
                        if q > 100:
                            aggregated['machinery'].add('Concrete Pump')
                        aggregated['vehicles'].add('Bulk Cement Truck')
                        # scale labour
                        aggregated['labour']['skilled'] += mixers
                        aggregated['labour']['unskilled'] += max(2, int(math.ceil(q / 20)))
                        # heuristic labour roles
                        heuristic_roles.add('mason')
                        heuristic_roles.add('operator')
                    else:
                        # default fallback
                        aggregated['machinery'].add('Concrete Mixer')
                        aggregated['vehicles'].add('Bulk Cement Truck')
                        aggregated['labour']['skilled'] += 1
                        aggregated['labour']['unskilled'] += 2
                        heuristic_roles.add('mason')

                if name and name in ('sand', 'aggregate'):
                    q = qty or 0
                    aggregated['machinery'].add('Loader')
                    aggregated['vehicles'].add('Tipper Truck')
                    if unit and unit.lower() in ('m3', 'm'):
                        import math
                        aggregated['labour']['skilled'] += 0
                        aggregated['labour']['unskilled'] += max(1, int(math.ceil(q / 20)))
                        heuristic_roles.add('operator')
                        heuristic_roles.add('labourer')
                    else:
                        aggregated['labour']['unskilled'] += 2
                        heuristic_roles.add('labourer')

                if name and name in ('brick', 'block'):
                    q = qty or 0
                    aggregated['vehicles'].add('Small Truck')
                    # labour scales with brick count
                    if q:
                        import math
                        aggregated['labour']['skilled'] += max(1, int(math.ceil(q / 1000)))
                        aggregated['labour']['unskilled'] += max(3, int(math.ceil(q / 500)))
                        heuristic_roles.add('mason')
                        heuristic_roles.add('labourer')
                    else:
                        aggregated['labour']['skilled'] += 1
                        aggregated['labour']['unskilled'] += 6
                        heuristic_roles.add('mason')

                if name and name in ('tile',):
                    aggregated['vehicles'].add('Small Truck')
                    aggregated['labour']['skilled'] += 2
                    aggregated['labour']['unskilled'] += 2
                    heuristic_roles.add('labourer')
            except Exception:
                # ignore heuristic failures
                pass

        # If ML models present, try to use them for more nuanced predictions
        if 'vectorizer' in self.models and 'clf' in self.models:
            try:
                vec_obj = self.models['vectorizer']
                # Hashing vectorizer may be stateless but stored; both provide .transform
                vec = vec_obj.transform([' '.join(material_texts)])
                mach_pred = self.models['clf'].predict(vec)
                # mach_pred is expected to be a binary array shape (1, n_labels)
                try:
                    labels = self.models['mlb_mach'].classes_
                    selected = [labels[i] for i, v in enumerate(mach_pred[0]) if v == 1]
                    aggregated['machinery'].update(selected)
                except Exception:
                    selected = []

                # Predict labour counts and use them to set minimum required labour
                try:
                    if self.models.get('reg') is not None:
                        lab_pred = self.models['reg'].predict(vec)[0]
                        aggregated['labour']['skilled'] = max(aggregated['labour']['skilled'], int(round(lab_pred[0])))
                        aggregated['labour']['unskilled'] = max(aggregated['labour']['unskilled'], int(round(lab_pred[1])))
                except Exception:
                    pass

                # Predict labour roles if model available
                if 'clf_roles' in self.models and 'mlb_roles' in self.models:
                    try:
                        roles_pred = self.models['clf_roles'].predict(vec)
                        role_labels = self.models['mlb_roles'].classes_
                        selected_roles = [role_labels[i] for i, v in enumerate(roles_pred[0]) if v == 1]
                        aggregated_roles = set(selected_roles)
                    except Exception:
                        aggregated_roles = set()
                else:
                    aggregated_roles = set()
            except Exception:
                aggregated_roles = set()
        else:
            aggregated_roles = set()

        # Combine heuristic roles with ML-predicted roles
        # Heuristic roles: collected in heuristic_roles set
        role_type_map = {
            'mason': 'skilled',
            'welder': 'skilled',
            'operator': 'skilled',
            'supervisor': 'skilled',
            'labourer': 'unskilled'
        }

        combined_roles = set(heuristic_roles) | set(aggregated_roles)
        final_roles = sorted(list(combined_roles))
        final_role_types = {r: role_type_map.get(r, 'unskilled') for r in final_roles}

        return {
            'machinery': sorted(list(aggregated['machinery'])),
            'vehicles': sorted(list(aggregated['vehicles'])),
            'labour': aggregated['labour'],
            'labour_roles': final_roles,
            'labour_role_types': final_role_types
        }

if __name__ == '__main__':
    # Quick manual test
    p = Predictor()
    s = "Supply and lay 50 m3 concrete (cement: 5 ton, sand: 1.5 m3) using ACC brand cement"
    parsed = {'materials': [{'raw': s, 'material': 'cement', 'quantity': 50, 'unit': 'm3', 'brands': ['ACC']}], 'raw_text': s}
    print(p.predict(parsed))
