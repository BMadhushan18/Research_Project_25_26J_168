"""
Cost Estimation & Waste Reduction Recommendations
Generates logistics cost estimates and AI-backed suggestions.
"""

from typing import List
from models.schemas import CostEstimate, WasteRecommendation


# ─── Sri Lankan Market Rates (LKR) ───────────────────────────────────
RATES = {
    # Vehicles — daily hire rate
    "light_vehicle_day": 8_000,
    "medium_truck_day": 18_000,
    "heavy_truck_day": 28_000,
    "concrete_mixer_day": 22_000,
    "tipper_truck_day": 20_000,

    # Labor — daily wage
    "unskilled_day": 2_500,
    "semi_skilled_day": 3_500,
    "skilled_day": 5_000,
    "supervisor_day": 8_000,
    "engineer_day": 15_000,

    # Machinery — daily hire
    "excavator_day": 55_000,
    "bulldozer_day": 60_000,
    "crane_day": 80_000,
    "concrete_pump_day": 35_000,
    "compactor_day": 25_000,
    "scaffolding_set_day": 3_000,
}

# Project duration default for cost calc (days)
DEFAULT_DURATION = 90


def estimate_costs(
    vehicles: dict,
    labor: dict,
    machinery: dict,
    duration_days: int = DEFAULT_DURATION,
) -> CostEstimate:
    r = RATES

    vehicle_cost = (
        vehicles["light_vehicles"] * r["light_vehicle_day"] +
        vehicles["medium_trucks"] * r["medium_truck_day"] +
        vehicles["heavy_trucks"] * r["heavy_truck_day"] +
        vehicles["concrete_mixers"] * r["concrete_mixer_day"] +
        vehicles["tipper_trucks"] * r["tipper_truck_day"]
    ) * duration_days

    labor_cost = (
        labor["unskilled_workers"] * r["unskilled_day"] +
        labor["semi_skilled_workers"] * r["semi_skilled_day"] +
        labor["skilled_workers"] * r["skilled_day"] +
        labor["supervisors"] * r["supervisor_day"] +
        labor["engineers"] * r["engineer_day"]
    ) * duration_days

    machinery_cost = (
        machinery["excavators"] * r["excavator_day"] +
        machinery["bulldozers"] * r["bulldozer_day"] +
        machinery["cranes"] * r["crane_day"] +
        machinery["concrete_pumps"] * r["concrete_pump_day"] +
        machinery["compactors"] * r["compactor_day"] +
        machinery["scaffolding_sets"] * r["scaffolding_set_day"]
    ) * duration_days

    total = vehicle_cost + labor_cost + machinery_cost

    return CostEstimate(
        vehicle_cost_lkr=round(vehicle_cost, 2),
        labor_cost_lkr=round(labor_cost, 2),
        machinery_cost_lkr=round(machinery_cost, 2),
        total_logistics_cost_lkr=round(total, 2),
    )


def generate_waste_recommendations(features) -> List[WasteRecommendation]:
    """
    Rule-based waste reduction suggestions derived from BOQ feature analysis.
    In production this can be upgraded to call an LLM (GPT / Claude).
    """
    recommendations = []
    total_amount = float(features[0])
    concrete_qty = float(features[3])
    steel_qty = float(features[4])
    earthwork_qty = float(features[5])
    finishing_qty = float(features[7])
    has_road = bool(features[18])

    if concrete_qty > 200:
        recommendations.append(WasteRecommendation(
            category="Concrete",
            suggestion="Consider using Ready-Mix Concrete (RMC) suppliers to reduce on-site batching waste. "
                       "Prefabricated concrete elements can reduce material waste by up to 20%.",
            estimated_saving_percentage=15.0
        ))

    if steel_qty > 50:
        recommendations.append(WasteRecommendation(
            category="Steel / Reinforcement",
            suggestion="Use BIM-optimized cut lists for rebar to minimize offcuts. "
                       "Procure pre-cut and bent steel from licensed fabricators.",
            estimated_saving_percentage=8.0
        ))

    if earthwork_qty > 300:
        recommendations.append(WasteRecommendation(
            category="Earthworks",
            suggestion="Balance cut-and-fill operations on-site to reduce spoil disposal costs. "
                       "Surplus soil can be used for landscaping or sold to nearby projects.",
            estimated_saving_percentage=12.0
        ))

    if finishing_qty > 100:
        recommendations.append(WasteRecommendation(
            category="Finishing Materials",
            suggestion="Order tiles and flooring with a 5% overage instead of 10–15%. "
                       "Use rectified tiles to reduce grout joints and wastage.",
            estimated_saving_percentage=6.0
        ))

    if has_road:
        recommendations.append(WasteRecommendation(
            category="Road / Pavement",
            suggestion="Use cold-in-place recycling (CIR) for base layers where possible. "
                       "Reclaimed asphalt pavement (RAP) can replace up to 30% of virgin aggregate.",
            estimated_saving_percentage=18.0
        ))

    if total_amount > 50_000_000:
        recommendations.append(WasteRecommendation(
            category="Logistics Optimization",
            suggestion="Implement a centralized material scheduling system. "
                       "Consolidate deliveries using 20-ton trucks instead of multiple smaller loads "
                       "to reduce transportation costs and carbon footprint.",
            estimated_saving_percentage=10.0
        ))

    # Always include general recommendation
    recommendations.append(WasteRecommendation(
        category="General",
        suggestion="Adopt a Just-In-Time (JIT) delivery model for bulk materials to reduce on-site "
                   "storage, damage, and pilferage. Digital tracking of material receipts is recommended.",
        estimated_saving_percentage=5.0
    ))

    return recommendations
