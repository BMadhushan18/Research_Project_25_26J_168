from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, validator
from app.predictor import Predictor
from app.nlp_parser import parse_boq
from app.train_manager import start_background_job, get_job
import os
import logging
import aiofiles

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart Logistics Backend")

predictor = Predictor()
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))
os.makedirs(os.path.join(DATA_DIR, 'uploads'), exist_ok=True)

class PredictRequest(BaseModel):
    boq_text: str
    materials: list[str] | None = None

    @validator('boq_text')
    def validate_boq_text(cls, v):
        """Validate boq_text: non-empty and reasonable length."""
        if not v or not v.strip():
            raise ValueError('boq_text cannot be empty')
        if len(v) > 10000:
            raise ValueError('boq_text exceeds maximum length of 10,000 characters')
        return v.strip()

@app.post("/predict")
async def predict(req: PredictRequest):
    """Predict machinery, vehicles, and labour requirements from BOQ text.
    
    Returns:
        {
            "parsed": {...},
            "prediction": {
                "machinery": [...],
                "vehicles": [...],
                "labour": {"skilled": int, "unskilled": int},
                "labour_roles": [...],
                "labour_role_types": {...},
                "model_used": "ml" | "rules"
            }
        }
    """
    try:
        parsed = parse_boq(req.boq_text)
        # Allow user to override parsed materials if provided
        if req.materials:
            parsed['materials'] = req.materials
        result = predictor.predict(parsed)
        # Add indicator of which model was used
        result['model_used'] = 'ml' if predictor.model_loaded else 'rules'

        # Log prediction to MongoDB if available
        try:
            from app.db import get_db
            db = get_db()
            if db is not None:
                db.predictions.insert_one({
                    'created_at': __import__('datetime').datetime.utcnow(),
                    'raw_text': parsed.get('raw_text'),
                    'materials': parsed.get('materials'),
                    'prediction': result,
                    'model_used': result['model_used']
                })
        except Exception as e:
            logger.warning(f'Failed to log prediction to MongoDB: {e}')

        logger.info(f'Prediction completed using {result["model_used"]} model')
        return {"parsed": parsed, "prediction": result}
    except Exception as e:
        logger.error(f'Prediction failed: {e}')
        raise HTTPException(status_code=500, detail=f'Prediction failed: {str(e)}')


@app.post('/train')
async def train_endpoint(file: UploadFile = File(...), background: bool = True, bg_tasks: BackgroundTasks = BackgroundTasks()):
    """Upload a CSV and trigger training (sync or async).

    - `file` should be a CSV with columns: `boq_text,machinery,vehicles,skilled,unskilled,labour_roles` (see `data/training_for_model.csv`).
    - If `background=true` (default), training runs asynchronously; returns job_id.
    - If `background=false`, training runs synchronously; returns status on completion.
    
    Required columns: boq_text, machinery, vehicles, skilled, unskilled
    Optional columns: labour_roles
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail='No filename provided')
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail='Only CSV files supported; file must end in .csv')
    
    # Validate file size (max 100 MB)
    if file.size and file.size > 100 * 1024 * 1024:
        raise HTTPException(status_code=413, detail='File exceeds maximum size of 100 MB')

    save_name = f"upload_{file.filename}"
    save_path = os.path.join(DATA_DIR, 'uploads', save_name)

    # Save file
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        async with aiofiles.open(save_path, 'wb') as out_f:
            content = await file.read()
            if not content:
                raise ValueError('Uploaded file is empty')
            await out_f.write(content)
        logger.info(f'Saved uploaded file to {save_path} ({len(content)} bytes)')
    except Exception as e:
        logger.error(f'Failed to save uploaded file: {e}')
        raise HTTPException(status_code=500, detail=f'Failed to save uploaded file: {str(e)}')

    try:
        if background:
            job_id = start_background_job(save_path, out_dir=MODELS_DIR, bg_tasks=bg_tasks)
            logger.info(f'Started background training job {job_id}')
            return {"job_id": job_id, "status": "queued"}
        else:
            # run inline
            job_id = start_background_job(save_path, out_dir=MODELS_DIR, bg_tasks=None)
            job = get_job(job_id)
            if job.get('status') == 'completed':
                logger.info(f'Synchronous training job {job_id} completed')
                return {"job_id": job_id, "status": "completed", "metadata": job.get('metadata')}
            else:
                logger.error(f'Synchronous training job {job_id} failed: {job.get("error")}')
                raise HTTPException(status_code=500, detail={"status": job.get('status'), "error": job.get('error')})
    except Exception as e:
        logger.error(f'Training endpoint error: {e}')
        raise HTTPException(status_code=500, detail=f'Training failed: {str(e)}')


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
