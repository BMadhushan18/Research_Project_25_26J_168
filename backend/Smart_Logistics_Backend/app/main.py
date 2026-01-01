from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from app.predictor import Predictor
from app.nlp_parser import parse_boq
from app.train_manager import start_background_job, get_job
import os
import aiofiles

app = FastAPI(title="Smart Logistics Backend")

predictor = Predictor()
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))
os.makedirs(os.path.join(DATA_DIR, 'uploads'), exist_ok=True)

class PredictRequest(BaseModel):
    boq_text: str
    materials: list[str] | None = None

@app.post("/predict")
async def predict(req: PredictRequest):
    parsed = parse_boq(req.boq_text)
    # Allow user to override parsed materials if provided
    if req.materials:
        parsed['materials'] = req.materials
    result = predictor.predict(parsed)

    # Log prediction to MongoDB if available
    try:
        from app.db import get_db
        db = get_db()
        if db is not None:
            db.predictions.insert_one({
                'created_at': __import__('datetime').datetime.utcnow(),
                'raw_text': parsed.get('raw_text'),
                'materials': parsed.get('materials'),
                'prediction': result
            })
    except Exception:
        # Logging should not interfere with API response
        pass

    return {"parsed": parsed, "prediction": result}


@app.post('/train')
async def train_endpoint(file: UploadFile = File(...), background: bool = True, bg_tasks: BackgroundTasks = BackgroundTasks()):
    # `bg_tasks` will be provided by FastAPI when available; we use it to schedule background training.
    """Upload a CSV and trigger training.

    - `file` should be a CSV with columns: `boq_text,machinery,vehicles,skilled,unskilled` (see `data/training_for_model.csv`).
    - If `background=true` (default), training is scheduled in FastAPI BackgroundTasks and an asynchronous job id is returned.
    - If `background=false`, training runs synchronously and the response completes after training finishes.
    """
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Only CSV uploads supported')

    save_name = f"upload_{file.filename}"
    save_path = os.path.join(DATA_DIR, 'uploads', save_name)

    # Save file
    try:
        async with aiofiles.open(save_path, 'wb') as out_f:
            content = await file.read()
            await out_f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to save uploaded file: {e}')

    if background:
        job_id = start_background_job(save_path, out_dir=MODELS_DIR, bg_tasks=bg_tasks)
        return {"job_id": job_id, "status": "queued"}
    else:
        # run inline
        job_id = start_background_job(save_path, out_dir=MODELS_DIR, bg_tasks=None)
        job = get_job(job_id)
        if job.get('status') == 'completed':
            return {"status": "completed"}
        else:
            raise HTTPException(status_code=500, detail={"status": job.get('status'), "error": job.get('error')})


@app.get('/train/{job_id}')
def train_status(job_id: str):
    return get_job(job_id)


@app.get('/db/health')
def db_health():
    """Return MongoDB connectivity status."""
    try:
        from app.db import is_available
        available = is_available()
    except Exception:
        available = False
    return {"available": bool(available)}
