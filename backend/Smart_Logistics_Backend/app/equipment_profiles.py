"""Reference fuel consumption profiles for common construction vehicles and machinery.

The predictor uses these lookup values to estimate daily fuel demand for
both vehicles and heavy machinery even when quantities are not explicitly
provided in the BOQ text.
"""
from __future__ import annotations

from typing import Dict, Any

DEFAULT_FUEL_PROFILE: Dict[str, Any] = {
    "name": "Generic Equipment",
    "category": "machinery",
    "fuel_type": "Diesel",
    "liters_per_shift": 25.0,
    "notes": "Baseline consumption for mid-sized diesel equipment",
}


EQUIPMENT_FUEL_LIBRARY: Dict[str, Dict[str, Any]] = {
    "tipper truck": {
        "name": "Tipper Truck",
        "category": "vehicle",
        "fuel_type": "Diesel",
        "liters_per_shift": 45.0,
        "notes": "10T tipper hauling aggregates",
        "aliases": ["tipper", "dump truck", "dumptruck"],
    },
    "dump truck": {
        "name": "Dump Truck",
        "category": "vehicle",
        "fuel_type": "Diesel",
        "liters_per_shift": 50.0,
        "notes": "Heavy dump truck for demolition debris",
        "aliases": ["haul truck"],
    },
    "pickup truck": {
        "name": "Pickup Truck",
        "category": "vehicle",
        "fuel_type": "Diesel",
        "liters_per_shift": 18.0,
        "notes": "Double-cab diesel pickup for supervisors",
        "aliases": ["pickup"],
    },
    "panel van": {
        "name": "Panel Van",
        "category": "vehicle",
        "fuel_type": "Diesel",
        "liters_per_shift": 16.0,
        "notes": "Light-duty logistics van",
    },
    "small truck": {
        "name": "Small Truck",
        "category": "vehicle",
        "fuel_type": "Diesel",
        "liters_per_shift": 22.0,
        "notes": "3.5T truck for block and tile delivery",
    },
    "large truck": {
        "name": "Large Truck",
        "category": "vehicle",
        "fuel_type": "Diesel",
        "liters_per_shift": 55.0,
        "notes": "Flatbed >12T logistics",
    },
    "bulk cement truck": {
        "name": "Bulk Cement Truck",
        "category": "vehicle",
        "fuel_type": "Diesel",
        "liters_per_shift": 52.0,
        "notes": "Pressurised bulk cement tanker",
    },
    "concrete mixer truck": {
        "name": "Concrete Mixer Truck",
        "category": "vehicle",
        "fuel_type": "Diesel",
        "liters_per_shift": 60.0,
        "notes": "8m3 transit mixer",
        "aliases": ["transit mixer", "rmc truck"],
    },
    "concrete mixer": {
        "name": "Concrete Mixer",
        "category": "machinery",
        "fuel_type": "Diesel",
        "liters_per_shift": 28.0,
        "notes": "On-site drum mixer",
    },
    "concrete pump": {
        "name": "Concrete Pump",
        "category": "machinery",
        "fuel_type": "Diesel",
        "liters_per_shift": 65.0,
        "notes": "Boom pump 36m class",
    },
    "vibrator": {
        "name": "Concrete Vibrator",
        "category": "machinery",
        "fuel_type": "Petrol",
        "liters_per_shift": 8.0,
        "notes": "Petrol-driven needle vibrator",
    },
    "loader": {
        "name": "Loader",
        "category": "machinery",
        "fuel_type": "Diesel",
        "liters_per_shift": 40.0,
        "notes": "1.5m3 bucket wheel loader",
        "aliases": ["wheel loader"],
    },
    "excavator": {
        "name": "Excavator",
        "category": "machinery",
        "fuel_type": "Diesel",
        "liters_per_shift": 65.0,
        "notes": "20T crawler excavator",
    },
    "bulldozer": {
        "name": "Bulldozer",
        "category": "machinery",
        "fuel_type": "Diesel",
        "liters_per_shift": 70.0,
        "notes": "Mid-size crawler dozer",
    },
    "vibratory roller": {
        "name": "Vibratory Roller",
        "category": "machinery",
        "fuel_type": "Diesel",
        "liters_per_shift": 48.0,
        "notes": "12T smooth drum roller",
    },
    "scissor lift": {
        "name": "Scissor Lift",
        "category": "machinery",
        "fuel_type": "Electric",
        "liters_per_shift": 0.0,
        "notes": "Battery operated access platform",
    },
    "boom lift": {
        "name": "Boom Lift",
        "category": "machinery",
        "fuel_type": "Diesel",
        "liters_per_shift": 30.0,
    },
    "tower crane": {
        "name": "Tower Crane",
        "category": "machinery",
        "fuel_type": "Electric",
        "liters_per_shift": 0.0,
        "notes": "Grid-powered tower crane",
    },
    "mobile crane": {
        "name": "Mobile Crane",
        "category": "machinery",
        "fuel_type": "Diesel",
        "liters_per_shift": 75.0,
        "notes": "50T hydraulic crane",
    },
    "crane": {
        "name": "Crane",
        "category": "machinery",
        "fuel_type": "Diesel",
        "liters_per_shift": 60.0,
        "notes": "General crawler / mobile crane",
    },
    "low-bed trailer": {
        "name": "Low-bed Trailer",
        "category": "vehicle",
        "fuel_type": "Diesel",
        "liters_per_shift": 58.0,
        "notes": "Heavy haul tractor with low-bed",
        "aliases": ["lowbed", "low bed trailer", "trailer"],
    },
    "trailer": {
        "name": "Trailer",
        "category": "vehicle",
        "fuel_type": "Diesel",
        "liters_per_shift": 40.0,
        "notes": "General haulage trailer",
    },
    "panel truck": {
        "name": "Panel Truck",
        "category": "vehicle",
        "fuel_type": "Diesel",
        "liters_per_shift": 25.0,
    },
    "power tools": {
        "name": "Power Tools",
        "category": "machinery",
        "fuel_type": "Electric",
        "liters_per_shift": 0.0,
        "notes": "Corded/cordless tools running on grid or battery",
    },
    "vacuum sander": {
        "name": "Vacuum Sander",
        "category": "machinery",
        "fuel_type": "Electric",
        "liters_per_shift": 0.0,
        "notes": "Dust extraction sander used in interiors",
    },
    "laser level": {
        "name": "Laser Level",
        "category": "machinery",
        "fuel_type": "Battery",
        "liters_per_shift": 0.0,
    },
    "hvac lift": {
        "name": "HVAC Lift",
        "category": "machinery",
        "fuel_type": "Electric",
        "liters_per_shift": 0.0,
    },
    "formwork system": {
        "name": "Formwork System",
        "category": "machinery",
        "fuel_type": "None",
        "liters_per_shift": 0.0,
        "notes": "Modular formwork does not consume fuel",
    },
    "batching plant": {
        "name": "Batching Plant",
        "category": "machinery",
        "fuel_type": "Diesel",
        "liters_per_shift": 80.0,
        "notes": "Skid batching plant with diesel generator",
    },
    "water bowser": {
        "name": "Water Bowser",
        "category": "vehicle",
        "fuel_type": "Diesel",
        "liters_per_shift": 32.0,
    },
    "jack hammer": {
        "name": "Jack Hammer",
        "category": "machinery",
        "fuel_type": "Electric",
        "liters_per_shift": 0.0,
        "notes": "Typically powered off compressors or electric",
    },
    "bar bender": {
        "name": "Bar Bender",
        "category": "machinery",
        "fuel_type": "Electric",
        "liters_per_shift": 0.0,
    },
    "concrete mixer;concrete pump": {
        "name": "Concrete Mixer & Pump",
        "category": "machinery",
        "fuel_type": "Diesel",
        "liters_per_shift": 85.0,
        "aliases": ["Concrete Mixer;Concrete Pump"],
    },
}


def _normalize(name: str) -> str:
    return (name or "").strip().lower()


def resolve_equipment_profile(name: str) -> Dict[str, Any]:
    """Return the canonical fuel profile for the given equipment name."""
    key = _normalize(name)
    if not key:
        return DEFAULT_FUEL_PROFILE.copy()
    if key in EQUIPMENT_FUEL_LIBRARY:
        entry = EQUIPMENT_FUEL_LIBRARY[key]
        return {**entry}
    for entry in EQUIPMENT_FUEL_LIBRARY.values():
        for alias in entry.get("aliases", []):
            if key == _normalize(alias):
                return {**entry}
    fallback = DEFAULT_FUEL_PROFILE.copy()
    fallback["name"] = name or DEFAULT_FUEL_PROFILE["name"]
    fallback["category"] = fallback.get("category") or "machinery"
    return fallback
