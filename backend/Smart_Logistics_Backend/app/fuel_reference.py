"""Sri Lankan fuel grade reference data for logistics planning.

This module captures the available petrol/diesel grades, auxiliary fuels,
key suppliers and emerging alternatives so that prediction responses can
surface localised recommendations.
"""
from __future__ import annotations

from typing import Dict, List

KEY_FUEL_SUPPLIERS: List[str] = [
    "Ceylon Petroleum Corporation (CEYPETCO)",
    "Lanka IOC PLC (LIOC)",
    "LAUGFS Petroleum",
]

LIGHT_FUEL_GRADES: Dict[str, List[Dict[str, str]]] = {
    "Petrol": [
        {
            "grade": "92 Octane",
            "alias": "Standard Petrol",
            "description": "Widely available petrol for light vehicles and generators",
            "suppliers": KEY_FUEL_SUPPLIERS,
        },
        {
            "grade": "95 Octane (Euro 4)",
            "alias": "Premium Petrol",
            "description": "High-octane petrol suited for modern engines and reduced knocking",
            "suppliers": KEY_FUEL_SUPPLIERS,
        },
    ],
    "Diesel": [
        {
            "grade": "Auto Diesel (Lanka Auto Diesel)",
            "alias": "Standard Diesel",
            "description": "Conventional diesel for trucks, buses and site equipment",
            "suppliers": KEY_FUEL_SUPPLIERS,
        },
        {
            "grade": "Super Diesel (Lanka Super Diesel 4 Star Euro 4)",
            "alias": "Premium Diesel",
            "description": "Low-sulfur diesel providing cleaner combustion for Euro 4 engines",
            "suppliers": KEY_FUEL_SUPPLIERS,
        },
    ],
}

OTHER_FUEL_TYPES: List[Dict[str, str]] = [
    {
        "fuel": "Kerosene",
        "description": "Lighting, cooking fuel and select industrial burners",
    },
    {
        "fuel": "Fuel Oil (Black Oil)",
        "description": "Heavy fuel for power plants and large industrial boilers",
    },
    {
        "fuel": "Lubricants & Greases",
        "description": "Engine oils, transmission fluids and maintenance consumables",
    },
    {
        "fuel": "Aviation Turbine Fuel (ATF)",
        "description": "Jet fuel for aircraft and select turbine-driven equipment",
    },
]

EMERGING_FUELS: List[Dict[str, str]] = [
    {
        "fuel": "Biofuels (Biodiesel / Biomass)",
        "description": "Pilots and sustainability programs using FAME or biomass blends",
    },
    {
        "fuel": "LPG (Liquefied Petroleum Gas)",
        "description": "Cylinder-based supply for cooking or specialised burners",
    },
    {
        "fuel": "CNG / LNG",
        "description": "Natural gas options under evaluation for transport fleets",
    },
]

FUEL_GRADE_REFERENCE: Dict[str, List[Dict[str, str]]] = {}
FUEL_GRADE_REFERENCE.update(LIGHT_FUEL_GRADES)
FUEL_GRADE_REFERENCE["Kerosene"] = [OTHER_FUEL_TYPES[0]]
FUEL_GRADE_REFERENCE["Fuel Oil"] = [OTHER_FUEL_TYPES[1]]
FUEL_GRADE_REFERENCE["Lubricants"] = [OTHER_FUEL_TYPES[2]]
FUEL_GRADE_REFERENCE["ATF"] = [OTHER_FUEL_TYPES[3]]
FUEL_GRADE_REFERENCE["Biofuel"] = [EMERGING_FUELS[0]]
FUEL_GRADE_REFERENCE["LPG"] = [EMERGING_FUELS[1]]
FUEL_GRADE_REFERENCE["CNG"] = [EMERGING_FUELS[2]]
FUEL_GRADE_REFERENCE["Electric"] = [
    {
        "grade": "Grid Power / Battery",
        "description": "Electrical supply (CEB/LECO grid or on-site battery banks)",
    }
]
FUEL_GRADE_REFERENCE["Battery"] = FUEL_GRADE_REFERENCE["Electric"]
FUEL_GRADE_REFERENCE["None"] = [
    {
        "grade": "Mechanical",
        "description": "Equipment that does not consume fuel (e.g., passive formwork)",
    }
]
