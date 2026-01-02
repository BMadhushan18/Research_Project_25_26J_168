"""Utility to augment the training dataset with curated Sri Lankan
examples and new work-type coverage (slab pours, interior fit-out).

Run from the backend folder:

    python scripts/augment_training_data.py \
        --data data/training_for_model.csv \
        --curated data/training_sl_curated_2026.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Dict

import pandas as pd


NEW_ROWS: List[Dict[str, object]] = [
    {
        "boq_text": "SL 2026: Interior fit-out for corporate HQ with gypsum ceilings, timber flooring, smart lighting and acoustic partitions",
        "machinery": "Scissor Lift;Power Tools;Vacuum Sander",
        "vehicles": "Pickup Truck;Panel Van",
        "skilled": 12,
        "unskilled": 6,
        "labour_roles": "interior_designer;drywall_carpenter;ceiling_installer;finishing_carpenter;painter;electrician_fitout;plumber_fitout;interior_helper",
    },
    {
        "boq_text": "SL 2026: Luxury apartment interiors VRF HVAC commissioning, bespoke joinery and quartz counters",
        "machinery": "HVAC Lift;Power Tools;Laser Level",
        "vehicles": "Panel Van",
        "skilled": 14,
        "unskilled": 5,
        "labour_roles": "interior_designer;finishing_carpenter;hvac_technician;electrician_fitout;plumber_fitout;painter;interior_helper",
    },
    {
        "boq_text": "SL 2026: Night pour slab concreting for podium deck 180 m3 with boom pump and reusable table formwork",
        "machinery": "Concrete Pump;Concrete Mixer;Vibrator;Formwork System",
        "vehicles": "Concrete Mixer Truck;Tipper Truck",
        "skilled": 16,
        "unskilled": 14,
        "labour_roles": "formwork_carpenter;steel_fixer;concrete_pump_operator;concrete_vibrator_operator;batcher_helper;general_labourer_slab;site_engineer_slab;safety_officer_slab",
    },
    {
        "boq_text": "SL 2026: Raft foundation slab pour using tower crane to place reinforcement and onsite batching plant output",
        "machinery": "Tower Crane;Batching Plant;Concrete Pump;Vibrator",
        "vehicles": "Concrete Mixer Truck;Low-bed Trailer",
        "skilled": 18,
        "unskilled": 16,
        "labour_roles": "formwork_carpenter;steel_fixer;concrete_pump_operator;concrete_vibrator_operator;batcher_helper;general_labourer_slab;site_engineer_slab;safety_officer_slab",
    },
    {
        "boq_text": "SL 2026: Highway embankment earthworks with 20 tipper rotations, wheel loader stockpiles and padfoot roller compaction",
        "machinery": "Excavator;Loader;Vibratory Roller",
        "vehicles": "Tipper Truck;Dump Truck;Pickup Truck",
        "skilled": 10,
        "unskilled": 18,
        "labour_roles": "operator_skilled;surveyor_skilled;welder_skilled;driver_unskilled;labourer_unskilled",
    },
    {
        "boq_text": "SL 2026: Remote hilltop wind farm concrete bases with mixer convoy, water bowser curing and low-bed crane mobilisation",
        "machinery": "Concrete Pump;Concrete Mixer;Vibrator",
        "vehicles": "Concrete Mixer Truck;Water Bowser;Low-bed Trailer",
        "skilled": 17,
        "unskilled": 12,
        "labour_roles": "formwork_carpenter;steel_fixer;concrete_pump_operator;concrete_vibrator_operator;driver_unskilled;labourer_unskilled;site_engineer_slab",
    },
]


def augment_dataset(data_path: Path, curated_path: Path) -> int:
    df_base = pd.read_csv(data_path)
    curated = pd.read_csv(curated_path)
    curated = curated.dropna(subset=["boq_text"])
    df_new = pd.DataFrame(NEW_ROWS)

    combined = pd.concat([df_base, curated, df_new], ignore_index=True)
    for column in ["machinery", "vehicles", "labour_roles"]:
        combined[column] = combined[column].fillna('')

    combined = combined.drop_duplicates(subset=["boq_text"], keep="last").reset_index(drop=True)
    combined.to_csv(data_path, index=False)
    return len(combined)


def main() -> None:
    parser = argparse.ArgumentParser(description="Augment training CSV with curated rows")
    parser.add_argument("--data", default="data/training_for_model.csv", help="Path to the base training CSV")
    parser.add_argument("--curated", default="data/training_sl_curated_2026.csv", help="Path to curated dataset with Sri Lankan roles")
    args = parser.parse_args()

    data_path = Path(args.data)
    curated_path = Path(args.curated)
    count = augment_dataset(data_path, curated_path)
    print(f"Wrote {count} rows to {data_path}")


if __name__ == "__main__":
    main()
