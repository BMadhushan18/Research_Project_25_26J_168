"""
Feature Engineering for BOQ → ML Models

Extracts and normalizes features from raw BOQ data to feed into
the pre-trained Random Forest models.
"""

import re
import numpy as np
from typing import List, Dict, Any
from models.schemas import BOQItem


# ─── Keyword Maps ────────────────────────────────────────────────────

MATERIAL_KEYWORDS = {
    "concrete": ["concrete", "rcc", "pcc", "cement", "mortar", "grout"],
    "steel": ["steel", "rebar", "reinforcement", "rod", "bar", "iron"],
    "masonry": ["brick", "block", "masonry", "stone", "rubble"],
    "earthwork": ["excavation", "filling", "backfill", "grading", "earth", "soil", "cut", "fill"],
    "finishing": ["plaster", "paint", "tile", "flooring", "render", "screed"],
    "formwork": ["formwork", "shuttering", "framework", "falsework"],
    "roofing": ["roof", "roofing", "sheet", "truss", "purlin"],
    "plumbing": ["pipe", "plumbing", "drainage", "sewage", "water supply", "sanitary"],
    "electrical": ["electrical", "wiring", "cable", "conduit", "panel", "switchboard"],
    "structural": ["column", "beam", "slab", "foundation", "footing", "pile"],
    "road": ["road", "pavement", "asphalt", "bitumen", "kerb", "carriageway"],
    "landscaping": ["landscape", "garden", "grass", "plantation", "irrigation"],
}

UNIT_WEIGHTS_KG = {
    "m3": 2400,    # concrete/earth average
    "ton": 1000,
    "kg": 1,
    "m2": 50,      # approximate surface density
    "m": 20,
    "nos": 10,
    "lump": 500,
    "ls": 500,
    "cum": 2400,
    "sqm": 50,
    "rmt": 20,
}


def _normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _matches_keyword(description: str, keyword: str) -> bool:
    normalized_desc = _normalize_text(description)
    normalized_keyword = _normalize_text(keyword)
    if not normalized_desc or not normalized_keyword:
        return False
    if " " in normalized_keyword:
        return normalized_keyword in normalized_desc
    tokens = normalized_desc.split()
    return normalized_keyword in tokens


def extract_features(
    items: List[BOQItem],
    project_type: str = "building",
    duration_days: int = 90,
    site_location: str = "Colombo",
) -> np.ndarray:
    """
    Convert a list of BOQ items into a fixed-length feature vector
    compatible with the pre-trained models.

    Feature vector layout (20 features):
    [0]  total_amount
    [1]  total_quantity
    [2]  item_count
    [3]  concrete_qty
    [4]  steel_qty
    [5]  earthwork_qty
    [6]  masonry_qty
    [7]  finishing_qty
    [8]  structural_qty
    [9]  road_qty
    [10] estimated_weight_tons
    [11] duration_days
    [12] project_type_encoded
    [13] location_encoded
    [14] avg_unit_rate
    [15] max_single_item_amount
    [16] concrete_ratio
    [17] earthwork_ratio
    [18] has_road_work  (0/1)
    [19] has_heavy_materials (0/1)
    """

    category_qtys: Dict[str, float] = {k: 0.0 for k in MATERIAL_KEYWORDS}
    total_amount = 0.0
    total_quantity = 0.0
    total_weight_kg = 0.0
    unit_rates = []
    amounts = []

    for item in items:
        desc = item.description or ""
        qty = float(item.quantity or 0)
        rate = float(item.unit_rate or 0)
        amount = float(item.amount or (qty * rate))
        unit = (item.unit or "").lower().strip()

        total_amount += amount
        total_quantity += qty
        if rate > 0:
            unit_rates.append(rate)
        if amount > 0:
            amounts.append(amount)

        # Category tagging
        for category, keywords in MATERIAL_KEYWORDS.items():
            if any(_matches_keyword(desc, kw) for kw in keywords):
                category_qtys[category] += qty

        # Weight estimation
        weight_per_unit = UNIT_WEIGHTS_KG.get(unit, 10)
        total_weight_kg += qty * weight_per_unit

    item_count = len(items)
    avg_unit_rate = float(np.mean(unit_rates)) if unit_rates else 0.0
    max_amount = float(max(amounts)) if amounts else 0.0
    total_weight_tons = total_weight_kg / 1000.0

    concrete_ratio = (category_qtys["concrete"] / total_quantity) if total_quantity > 0 else 0
    earthwork_ratio = (category_qtys["earthwork"] / total_quantity) if total_quantity > 0 else 0

    project_type_map = {"building": 0, "road": 1, "bridge": 2, "civil": 3, "other": 4}
    project_type_enc = project_type_map.get(project_type.lower(), 0)

    location_map = {
        "colombo": 0, "gampaha": 1, "kalutara": 2, "kandy": 3,
        "galle": 4, "matara": 5, "negombo": 1, "kurunegala": 6,
        "anuradhapura": 7, "badulla": 8, "other": 9,
    }
    location_enc = location_map.get(site_location.lower().split(",")[0].strip(), 9)

    has_road_work = 1 if category_qtys["road"] > 0 else 0
    has_heavy = 1 if (category_qtys["concrete"] + category_qtys["steel"] + category_qtys["earthwork"]) > 100 else 0

    features = np.array([
        total_amount,
        total_quantity,
        float(item_count),
        category_qtys["concrete"],
        category_qtys["steel"],
        category_qtys["earthwork"],
        category_qtys["masonry"],
        category_qtys["finishing"],
        category_qtys["structural"],
        category_qtys["road"],
        total_weight_tons,
        float(duration_days),
        float(project_type_enc),
        float(location_enc),
        avg_unit_rate,
        max_amount,
        concrete_ratio,
        earthwork_ratio,
        float(has_road_work),
        float(has_heavy),
    ], dtype=np.float64)

    return features


def get_summary_stats(items: List[BOQItem]) -> Dict[str, Any]:
    """Return human-readable summary of the BOQ for response metadata."""
    total_amount = sum(
        float(i.amount or (i.quantity * (i.unit_rate or 0))) for i in items
    )
    total_quantity = sum(float(i.quantity) for i in items)
    return {
        "total_boq_amount": round(total_amount, 2),
        "total_quantity": round(total_quantity, 2),
        "item_count": len(items),
    }


def prepare_model_input(
    items: List[BOQItem],
    project_type: str = "building",
    duration_days: int = 90,
    site_location: str = "Colombo",
    total_floor_area_sqft: float = 5000.0,
    number_of_floors: int = 1,
    building_complexity_index: float = 5.0,
) -> "pd.DataFrame":
    """
    Build a per-item DataFrame matching the 9-feature schema the trained
    models expect.  Each row = one BOQ item with project-level context.

    Vehicle features:  quantity, task_description, unit, project_type,
                       site_location, total_floor_area_sqft,
                       number_of_floors, building_complexity_index,
                       project_duration_days

    Labor features:    quantity, measurement_type, project_type,
                       site_location, total_floor_area_sqft,
                       number_of_floors, building_complexity_index,
                       project_duration_days, task_description

    Machinery features: task_description, project_type, site_location,
                        unit, quantity, total_floor_area_sqft,
                        number_of_floors, building_complexity_index,
                        project_duration_days
    """
    import pandas as pd

    rows = []
    for item in items:
        rows.append({
            "quantity": float(item.quantity),
            "task_description": item.description or "",
            "unit": (item.unit or "nos").lower().strip(),
            "measurement_type": (item.unit or "nos").lower().strip(),
            "project_type": project_type.lower(),
            "site_location": site_location,
            "total_floor_area_sqft": float(total_floor_area_sqft),
            "number_of_floors": int(number_of_floors),
            "building_complexity_index": float(building_complexity_index),
            "project_duration_days": int(duration_days),
        })
    return pd.DataFrame(rows)
