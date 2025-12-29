# Full Prediction Model Specification
**Version:** 2025-12-29  
**Maintainer:** Madhushan S.M.P.B – IT22172532  
**Project ID:** 25-261-168  
**Title:** Building Plan Analysis, Material Estimate & Waste Reduction

## Purpose
This subsystem predicts required vehicles, labor (Unskilled/Semi-skilled/Skilled/Professional), drivers, fuel consumption, estimated hours, and total cost (LKR) for Sri Lankan construction projects.  
It uses:
- NLP parsing of BOQs (Excel) to extract quantities, rates, labor types, and vehicles
- Hybrid ML/DL + heuristic fallback for robust predictions
- Material → Task → Vehicle/Labor → Cost pipeline
- Sri Lanka-specific adjustments (monsoon delay, urban congestion, fuel ~350 LKR/L, 2025 labor rates)

## Final Training Dataset Headers (Used for Model Training)
These are the **exact columns** in the training CSV after processing the BOQ CSV and merging with the required schema.

```
sheet,item,description,quantity,unit,rate,amount,labor_types,vehicles,nlp_entities,total_fuel_liters,estimated_hours,estimated_cost_lkr,labor_hours,employee_count,
excavation_volume,site_area,wall_area,floor_area,concrete_volume,steel_quantity,brick_quantity,total_cement,total_sand,building_complexity,
Excavators,Bulldozers,Cranes,Dump Trucks,Loaders,Graders,Compactors,Pavers,Rollers,Trenchers,Skid Steers,Backhoe Loaders,Telehandlers,Forklifts,Scrapers,Concrete Mixers,Pile Drivers,Asphalt Mills,Manlifts,Drilling Rigs,
vehicles_needed,masons,welders,laborers,fuel_liters,estimated_hours,estimated_cost
```

**How it was created**:
- Parsed columns from the BOQ CSV (sheet, item, description, quantity, unit, rate, amount, labor_types, vehicles, nlp_entities, total_fuel_liters, estimated_hours, estimated_cost_lkr, labor_hours, employee_count)
- Added required schema columns (excavation_volume, site_area, etc., vehicle presence columns)
- Derived/synthesized missing numeric features (e.g., concrete_volume ≈ quantity when unit=m³)
- Generated target columns (vehicles_needed, masons, etc.) using heuristics + scaling from BOQ amounts

Total rows used for final training: **~200+** (BOQ-derived + synthetic augmentation to reach ~500 effective samples)

## Architecture & Integration Points
- Main logic: `smart_logistics_backend/utils/prediction.py`
- API endpoint: `POST /demo/predict` in `smart_logistics_backend/app.py`
- BOQ parser: `smart_logistics_backend/utils/extraction.py` (regex + spaCy NER)
- Training: `train_updated_model.py` (uses synthetic_boq.csv + augmentation)
- Models saved: `./trained_models/` (updated_ml_model.pkl, updated_dl_model.h5, updated_scaler.pkl)
- Config: `config.yaml` (recommended – labor rates, vehicle specs, multipliers)

## Inputs (DemoPredictionInput – Pydantic)
```python
class DemoPredictionInput(BaseModel):
    terrain: str = "urban"                      # urban / rural / flat / hilly / rough
    distance_km: float = 10.0                   # haul distance
    material_tons: float = None                 # simple fallback
    labor_type: str = "Skilled"                 # Unskilled / Semi-skilled / Skilled / Professional
    materials: List[MaterialItem] = []          # detailed materials (name, qty, unit...)
    wall: WallSpec = None                       # {length_m, height_m, thickness_m}
    target_days: int = 30                       # desired duration
    boq_file: UploadFile = None                 # Excel BOQ → auto-parsed
```

## Core Prediction Flow (Material-Driven – Preferred)
1. **BOQ Parsing (if uploaded)** → extract: quantity, rate, amount, labor_types (e.g., "Skilled,Semi-skilled"), vehicles (e.g., "Dump Truck,Excavator")
2. **Normalize Materials** → total_weight_tons, per-material kg/m³
3. **Task Estimation** → map materials to tasks (e.g., cement → Concrete pouring)
4. **Vehicle Allocation** → use TASK_VEHICLE_MAP + greedy by capacity
5. **Labor Allocation** → use LABOR_SKILL_MAP, spread across target_days
6. **Cost Calculation** → fuel + rental + driver + labor + SL adjustments
7. **Fallback** → if model fails: use heuristics

## Key Mappings (Hardcoded or in config.yaml)

**TASK_VEHICLE_MAP** (used for allocation):
```python
TASK_VEHICLE_MAP = {
    "Excavation & Earthwork": ["Excavator", "Bulldozer", "Dump Truck"],
    "Concrete Works": ["Concrete Mixer Truck", "Concrete Pump"],
    "Masonry & Blockwork": ["Tipper Truck", "Loader"],
    "Formwork & Shuttering": ["Flatbed Truck"],
    "Roofing": ["Flatbed Truck", "Mobile Crane"],
    "Tiling & Flooring": ["Tipper Truck"],
    "Plastering & Painting": ["Pickup Truck"],
    "Plumbing & Electrical": ["Pickup Truck"],
    "Waste Removal": ["Dump Truck"]
}
```

**LABOR_SKILL_MAP** (by task):
```python
LABOR_SKILL_MAP = {
    "Excavation": ["Unskilled", "Skilled (Operator)"],
    "Concrete": ["Skilled (Bar Bender)", "Semi-skilled", "Unskilled"],
    "Masonry": ["Skilled (Mason)", "Semi-skilled", "Unskilled"],
    "Plastering/Tiling": ["Skilled (Tiler/Mason)", "Semi-skilled"],
    "Painting": ["Skilled (Painter)", "Semi-skilled"],
    "Plumbing/Electrical": ["Skilled (Plumber/Electrician)", "Semi-skilled"],
    "Supervision": ["Professional (Foreman)"]
}
```

**VEHICLE_DETAILS** (fuel, rental, driver – daily rates 2025):
```python
VEHICLE_DETAILS = {
    "Excavator (Mid-Size)": {"fuel_per_hour_l": 12, "rental_daily_lkr": 30000, "driver_daily_lkr": 6000},
    "Dump Truck (10-Ton)": {"fuel_per_hour_l": 25, "rental_daily_lkr": 20000, "driver_daily_lkr": 5500},
    "Tipper Truck (6m³)": {"fuel_per_hour_l": 20, "rental_daily_lkr": 18000, "driver_daily_lkr": 5000},
    "Flatbed Truck": {"fuel_per_hour_l": 18, "rental_daily_lkr": 22000, "driver_daily_lkr": 6000},
    "Concrete Mixer Truck": {"fuel_per_hour_l": 30, "rental_daily_lkr": 35000, "driver_daily_lkr": 6500},
    "Mobile Crane": {"fuel_per_hour_l": 15, "rental_daily_lkr": 80000, "driver_daily_lkr": 9000}
}
```

**SL_ADJUSTMENTS** (Sri Lanka factors):
```python
SL_ADJUSTMENTS = {
    "urban": {"time_mult": 1.15, "cost_mult": 1.10},
    "rural": {"time_mult": 1.0, "cost_mult": 0.95},
    "monsoon": {"time_mult": 1.30, "cost_mult": 1.20},
    "fuel_price_lkr": 350,
    "labor_daily_rates": {
        "Unskilled": 4000,
        "Semi-skilled": 5500,
        "Skilled": 7000,
        "Professional": 15000
    },
    "driver_daily_rate": 5500
}
```

## Fallback Heuristics (when ML fails)
```python
FALLBACK_FORMULAS = {
    "vehicles_needed": lambda f: (f.get("concrete_volume", 0) / 50) + (f.get("steel_quantity", 0) / 500) + 2,
    "masons": lambda f: (f.get("concrete_volume", 0) / 20) + (f.get("site_area", 0) / 100) + 3,
    "laborers": lambda f: (f.get("concrete_volume", 0) / 10) + (f.get("site_area", 0) / 50) + 5,
    "fuel_liters": lambda f: (f.get("concrete_volume", 0) * 5) + (f.get("site_area", 0) * 0.5) + 100,
    "estimated_hours": lambda f: (f.get("concrete_volume", 0) * 10) + (f.get("site_area", 0) * 2) + 200,
    "estimated_cost": lambda f: (f.get("concrete_volume", 0) * 15000) + (f.get("steel_quantity", 0) * 200) + (f.get("site_area", 0) * 1000)
}
```

## Training Summary (Dec 29, 2025)
- **Data source**: `backend/Smart_Logistics_Backend/data/synthetic_boq.csv` (parsed) + synthetic augmentation
- **Total effective rows**: ~500 (BOQ-derived + generated)
- **Model types**: MultiOutput RandomForest (ML) + LSTM (DL)
- **Targets**: vehicles_needed, masons, welders, laborers, fuel_liters, estimated_hours, estimated_cost
- **Evaluation**: MAE ~5–15% on fuel/hours/cost; R² ~0.82–0.91
- **Best use**: Material-driven pipeline (with BOQ upload) for highest accuracy

## Operational Notes
- **Retraining**: Run `train_updated_model.py` anytime new BOQs are added
- **Config**: Example config: `backend/Smart_Logistics_Backend/config_example.yaml` (recommended to move into `config.yaml`)
- **Testing**: Use Postman with materials + BOQ upload (see `backend/Smart_Logistics_Backend/postman_collection.json` for examples)
- **Integration**: Example integration snippet: `backend/Smart_Logistics_Backend/examples/integration_snippet.py` demonstrates loading model and predicting from a BOQ CSV
- **Next steps**: Add route optimization, waste reduction suggestions

**End of Specification – Ready for Final Submission**
