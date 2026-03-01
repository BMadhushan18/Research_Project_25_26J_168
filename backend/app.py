from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from wood_predi import predict_wood
from paint_predi import predict_paint
from skimCoat_predi import predict_skimcoat

app = FastAPI(title="Construction Material Prediction API")

# Enable CORS for Flutter
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# Request Schemas
# =====================
class WoodRequest(BaseModel):
    price: float
    size: float
    location: str
    building_type: str


class PaintRequest(BaseModel):
    wall_size: float
    price_per_sqft: float
    location: str


class SkimCoatRequest(BaseModel):
    wall_size: float
    price_per_sqft: float
    location: str


# =====================
# API Endpoints
# =====================
@app.post("/predict/wood")
def wood_prediction(data: WoodRequest):
    return predict_wood(
        data.price,
        data.size,
        data.location,
        data.building_type
    )


@app.post("/predict/paint")
def paint_prediction(data: PaintRequest):
    return predict_paint(
        data.wall_size,
        data.price_per_sqft,
        data.location
    )


@app.post("/predict/skimcoat")
def skimcoat_prediction(data: SkimCoatRequest):
    return predict_skimcoat(
        data.wall_size,
        data.price_per_sqft,
        data.location
    )
