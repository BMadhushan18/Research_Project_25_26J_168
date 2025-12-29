from fastapi import FastAPI, File, UploadFile, Header, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from fastapi.responses import JSONResponse

app = FastAPI(title="Smart Logistics API (shim)", docs_url='/api/docs', redoc_url='/api/redoc')

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: Optional[str]
    username: Optional[str]

class DemoPredictionInput(BaseModel):
    terrain: Optional[str] = "urban"
    material_tons: Optional[float]

class DemoPredictionOutput(BaseModel):
    predicted_fuel_liters: float
    predicted_labor_hours: float
    total_estimated_cost_LKR: int
    message: Optional[str]

class ForecastRequest(BaseModel):
    material_demands: Dict[str,float]

class ForecastResponse(BaseModel):
    forecasts: Dict[str, Dict[str, float]]

@app.get("/", tags=["Health"])
def root():
    return {"status":"ok","version":"shim","timestamp":"now"}

@app.get("/health", tags=["Health"])
def health():
    return {"status":"ok"}

@app.get("/demo/health", tags=["Demo"])
def demo_health():
    return {"status":"demo ok"}

@app.post("/demo/predict", response_model=DemoPredictionOutput, tags=["Demo"])
def demo_predict(payload: DemoPredictionInput):
    # Simple deterministic mock response
    fuel = 10.0 * (payload.material_tons or 1.0)
    hours = 20.0 * (payload.material_tons or 1.0)
    cost = int(50000 * (payload.material_tons or 1.0))
    return DemoPredictionOutput(predicted_fuel_liters=fuel, predicted_labor_hours=hours, total_estimated_cost_LKR=cost, message="Prediction successful (shim)")

@app.post("/api/v1/login", response_model=TokenResponse, tags=["Authentication"])
def login(request: LoginRequest):
    # Shim: return a dummy token
    return TokenResponse(access_token="shim-token", token_type="bearer", user_id="user_1", username=request.username)

@app.post("/api/v1/upload-document", tags=["Document Processing"])
async def upload_document(file: UploadFile = File(...), project_name: Optional[str] = "Untitled Project", location_type: Optional[str] = "urban", authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Minimal response
    return JSONResponse({"project_id":"PROJ_SHIM_1","message":"Document processed (shim)","processing_time_seconds":0.1})

@app.post("/api/v1/forecast", response_model=ForecastResponse, tags=["Forecasting"])
def forecast(req: ForecastRequest, authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    out = {k: {"mean":v, "std": v*0.1, "p5": v*0.9, "p95": v*1.1} for k,v in req.material_demands.items()}
    return ForecastResponse(forecasts=out)

@app.post("/api/v1/optimize", tags=["Optimization"])
def optimize(payload: Dict, authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"optimized_routes": [], "cost_savings": 0}

@app.post("/api/v1/federated-update", tags=["Federated Learning"])
def federated_update(payload: Dict, authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"global_parameters": payload.get("model_parameters", {}), "aggregation_round": 1}

@app.get("/api/v1/projects/{user_id}", tags=["Projects"])
def list_projects(user_id: str, authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"user_id": user_id, "projects": [], "total_projects": 0}

@app.get("/api/v1/project/{project_id}", tags=["Projects"])
def get_project(project_id: str, authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"project_id": project_id, "details": {}}

@app.get("/api/v1/statistics", tags=["Statistics"])
def statistics(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"projects":0}

@app.post("/admin/reload-config", tags=["Admin"])
def reload_config(x_admin_token: Optional[str] = Header(None)):
    if x_admin_token != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"keys_loaded": []}
