from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict


# ─── Request Schemas ────────────────────────────────────────────────

class BOQItem(BaseModel):
    """A single BOQ line item"""
    description: str
    unit: Optional[str] = None
    quantity: float = Field(gt=0)
    unit_rate: Optional[float] = Field(default=None, ge=0)
    amount: Optional[float] = Field(default=None, ge=0)


class BOQTextInput(BaseModel):
    """Manual text / structured JSON input for BOQ"""
    project_name: Optional[str] = Field(default="Unnamed Project")
    project_type: Literal["building", "road", "bridge", "civil", "other"] = Field(default="building")
    project_duration_days: int = Field(default=90, ge=1, le=3650)
    site_location: Optional[str] = Field(default="Colombo")
    total_floor_area_sqft: float = Field(default=5000.0, ge=0)
    number_of_floors: int = Field(default=1, ge=1)
    building_complexity_index: float = Field(default=5.0, ge=1, le=10)
    items: List[BOQItem] = Field(min_length=1)


# ─── Response Schemas ────────────────────────────────────────────────

class VehiclePrediction(BaseModel):
    light_vehicles: int          # Cars / pickup trucks
    medium_trucks: int           # 5–10 ton
    heavy_trucks: int            # 10+ ton
    concrete_mixers: int
    tipper_trucks: int
    total_vehicles: int
    estimated_trips_per_day: int


class LaborPrediction(BaseModel):
    unskilled_workers: int
    semi_skilled_workers: int
    skilled_workers: int         # Carpenters, masons, etc.
    supervisors: int
    engineers: int
    total_headcount: int
    peak_daily_requirement: int


class MachineryPrediction(BaseModel):
    excavators: int
    bulldozers: int
    cranes: int
    concrete_pumps: int
    compactors: int
    scaffolding_sets: int
    estimated_machinery_hours_per_day: float
    total_equipment_units: int


class CostEstimate(BaseModel):
    vehicle_cost_lkr: float
    labor_cost_lkr: float
    machinery_cost_lkr: float
    total_logistics_cost_lkr: float
    currency: str = "LKR"


class WasteRecommendation(BaseModel):
    category: str
    suggestion: str
    estimated_saving_percentage: float


class PredictionResponse(BaseModel):
    project_name: str
    total_boq_amount: float
    total_quantity: float
    item_count: int
    vehicles: VehiclePrediction
    labor: LaborPrediction
    machinery: MachineryPrediction
    cost_estimate: CostEstimate
    waste_recommendations: List[WasteRecommendation]
    prediction_sources: Dict[str, str] = Field(default_factory=dict)
    model_version: str = "1.0.0"
    confidence_score: float


class ErrorResponse(BaseModel):
    detail: str
    error_code: str
