import re
from pathlib import Path
import pandas as pd
import spacy
from spacy.lang.en import English
from spacy.pipeline import EntityRuler

class DocumentExtractor:
    """Rule-based BOQ document extractor using spaCy's EntityRuler and regex helpers.
    It reads BOQ CSVs (with columns like 'item','description','quantity','unit','vehicles') and
    produces normalized numeric features used by the prediction model.
    """

    UNIT_MAP = {
        'bag': {'to_ton': 0.05},  # 50kg bag -> 0.05 ton
        'kg': {'to_ton': 0.001},
        'ton': {'to_ton': 1.0},
        'm3': {'to_m3': 1.0},
        'pcs': {'to_count': 1},
        'piece': {'to_count': 1}
    }

    VEHICLE_KEYWORDS = [
        'dump truck','excavator','concrete mixer','tipper truck','loader','bulldozer','crane','mobile crane','flatbed truck'
    ]

    MATERIAL_KEYWORDS = [
        'cement','steel','sand','bricks','gravel','concrete','tiles','paint','mortar'
    ]

    QUANTITY_RE = re.compile(r"(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>m3|ton|kg|bag|bags|pcs|piece|pieces)?", re.I)

    def __init__(self, nlp=None, patterns=None):
        self.nlp = nlp or English()
        # Add EntityRuler
        self.ruler = self.nlp.add_pipe('entity_ruler')
        patterns = patterns or self._default_patterns()
        self.ruler.add_patterns(patterns)

    def _default_patterns(self):
        pats = []
        for mat in self.MATERIAL_KEYWORDS:
            pats.append({"label":"MATERIAL","pattern":mat})
        for veh in self.VEHICLE_KEYWORDS:
            pats.append({"label":"VEHICLE","pattern":veh})
        return pats

    def parse_boq_csv(self, csv_path):
        p = Path(csv_path)
        if not p.exists():
            raise FileNotFoundError(f"BOQ file not found: {p}")
        df = pd.read_csv(p)
        # Clean column names
        df.columns = [c.strip() for c in df.columns]
        return df

    def extract_row_entities(self, text):
        doc = self.nlp(text.lower())
        entities = [ (ent.label_, ent.text) for ent in doc.ents ]
        return entities

    def parse_quantity(self, qty_val, unit_val):
        # If qty and unit available, use directly
        try:
            qty = float(qty_val)
        except Exception:
            # try regex on combined
            if isinstance(qty_val, str):
                m = self.QUANTITY_RE.search(qty_val)
                if m:
                    qty = float(m.group('qty'))
                    unit = m.group('unit')
                else:
                    return 0.0, None
            else:
                return 0.0, None
        unit = unit_val.lower() if isinstance(unit_val, str) else None
        return qty, unit

    def normalize_units(self, qty, unit):
        unit = (unit or '').lower() if unit else None
        if unit in ('bag','bags'):
            return qty * self.UNIT_MAP['bag']['to_ton']  # to tons
        if unit in ('kg',):
            return qty * self.UNIT_MAP['kg']['to_ton']
        if unit in ('ton',):
            return qty
        if unit in ('m3',):
            return qty
        # default
        return qty

    def compute_features(self, df):
        # Output aggregated features dict
        features = {
            'concrete_volume': 0.0,
            'steel_quantity': 0.0,
            'brick_quantity': 0.0,
            'total_cement_ton': 0.0,
            'total_sand_ton': 0.0,
            'site_area': 0.0,
            'wall_area': 0.0,
            'total_amount_lkr': 0.0,
            'vehicles_detected': {},
            'total_qty_sum': 0.0
        }
        # initialize vehicle flags
        for v in self.VEHICLE_KEYWORDS:
            features['vehicles_detected'][v] = 0

        for _, row in df.iterrows():
            item = str(row.get('item','')).lower()
            desc = str(row.get('description',''))
            qty_raw = row.get('quantity', 0)
            unit_raw = row.get('unit', '')
            qty, unit = self.parse_quantity(qty_raw, unit_raw)
            features['total_qty_sum'] += qty
            # normalize
            # concrete volume
            if 'concrete' in item or 'concrete' in desc.lower() or unit == 'm3':
                # concrete volume in m3
                if unit == 'm3':
                    features['concrete_volume'] += qty
                else:
                    # if unit is bag and item contains cement, approximate
                    features['concrete_volume'] += 0
            # steel
            if 'steel' in item or 'steel' in desc.lower():
                # assume qty is kg if unit kg, else tons if unit ton
                if unit == 'kg':
                    features['steel_quantity'] += qty
                elif unit == 'ton':
                    features['steel_quantity'] += qty * 1000
                else:
                    features['steel_quantity'] += qty
            # bricks count
            if 'brick' in item or 'brick' in desc.lower():
                features['brick_quantity'] += qty
            # cement
            if 'cement' in item or 'cement' in desc.lower():
                # convert bags to tons (assuming 1 bag = 50kg)
                if unit in ('bag','bags'):
                    features['total_cement_ton'] += qty * self.UNIT_MAP['bag']['to_ton']
                elif unit == 'kg':
                    features['total_cement_ton'] += qty * self.UNIT_MAP['kg']['to_ton']
                elif unit == 'ton':
                    features['total_cement_ton'] += qty
            # sand
            if 'sand' in item or 'sand' in desc.lower():
                if unit in ('m3', 'ton'):
                    features['total_sand_ton'] += qty
                elif unit in ('kg', 'bag'):
                    features['total_sand_ton'] += self.normalize_units(qty, unit)
            # area heuristics
            if 'area' in item or 'site' in item or 'site' in desc.lower():
                features['site_area'] += qty
            if 'wall' in item or 'wall' in desc.lower():
                # try to infer wall area from quantity if qty is linear metres and height present elsewhere
                features['wall_area'] += qty
            # vehicles
            vehicles_field = str(row.get('vehicles','')).lower()
            for v in self.VEHICLE_KEYWORDS:
                if v in vehicles_field or v in desc.lower() or v in item:
                    features['vehicles_detected'][v] += 1
            # amount
            amt = row.get('amount', 0)
            try:
                features['total_amount_lkr'] += float(amt)
            except Exception:
                pass
        # postprocess: create simple aggregates
        features['vehicles_total'] = sum(features['vehicles_detected'].values())
        # approximate site area fallback
        if features['site_area'] == 0 and features['total_qty_sum'] > 0:
            features['site_area'] = features['total_qty_sum'] * 0.1
        return features

    def extract_features_from_csv(self, csv_path):
        df = self.parse_boq_csv(csv_path)
        features = self.compute_features(df)
        return features


# quick manual test
if __name__ == '__main__':
    de = DocumentExtractor()
    feats = de.extract_features_from_csv(Path(__file__).resolve().parents[1] / 'data' / 'synthetic_boq.csv')
    print(feats)
