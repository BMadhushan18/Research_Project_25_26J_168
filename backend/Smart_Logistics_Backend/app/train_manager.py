import os
import logging
from uuid import uuid4
from typing import Dict
from fastapi import BackgroundTasks
from datetime import datetime

from app.db import get_db, is_available

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))

# Fallback in-memory store for environments without MongoDB
JOBS: Dict[str, dict] = {}


def run_training(file_path: str, out_dir: str = MODELS_DIR):
    """Run training synchronously using scripts/train.py utilities."""
    # Import here to avoid import cycles at module import time in tests
    from scripts.train import load_df, fit_and_save
    logger.info(f'Loading training data from {file_path}')
    df = load_df(file_path)
    logger.info(f'Loaded {len(df)} rows; starting training...')
    fit_and_save(df, out_dir)
    logger.info(f'Training complete; artifacts saved to {out_dir}')


def _runner(job_id: str, file_path: str, out_dir: str):
    """Background task runner for training jobs."""
    db = get_db()
    try:
        if db is not None:
            db.jobs.update_one({"job_id": job_id}, {"$set": {"status": "running", "started_at": datetime.utcnow()}}, upsert=True)
        else:
            JOBS[job_id] = {"status": "running"}
        
        logger.info(f'Starting training job {job_id}')
        run_training(file_path, out_dir)

        # Record completion and basic model metadata
        metadata = {"artifacts": os.listdir(out_dir), "completed_at": datetime.utcnow()}
        if db is not None:
            db.jobs.update_one({"job_id": job_id}, {"$set": {"status": "completed", "metadata": metadata}}, upsert=True)
            db.models.insert_one({"job_id": job_id, "metadata": metadata, "created_at": datetime.utcnow()})
            logger.info(f'Training job {job_id} completed; metadata logged to MongoDB')
        else:
            JOBS[job_id] = {"status": "completed", "metadata": metadata}
            logger.info(f'Training job {job_id} completed; metadata logged to memory')
    except Exception as e:
        logger.error(f'Training job {job_id} failed: {e}')
        if db:
            db.jobs.update_one({"job_id": job_id}, {"$set": {"status": "failed", "error": str(e), "failed_at": datetime.utcnow()}}, upsert=True)
        else:
            JOBS[job_id] = {"status": "failed", "error": str(e)}


def start_background_job(file_path: str, out_dir: str = MODELS_DIR, bg_tasks: BackgroundTasks = None) -> str:
    """Create and start a training job (async or inline)."""
    job_id = uuid4().hex
    db = get_db()
    if db is not None:
        db.jobs.insert_one({"job_id": job_id, "status": "queued", "file_path": file_path, "created_at": datetime.utcnow()})
        logger.info(f'Job {job_id} queued in MongoDB')
    else:
        JOBS[job_id] = {"status": "queued", "file_path": file_path}
        logger.info(f'Job {job_id} queued in memory')

    if bg_tasks:
        bg_tasks.add_task(_runner, job_id, file_path, out_dir)
        logger.info(f'Job {job_id} scheduled for background execution')
    else:
        # fallback: run inline
        _runner(job_id, file_path, out_dir)
    return job_id


def get_job(job_id: str):
    """Retrieve job status and metadata."""
    db = get_db()
    if db is not None:
        doc = db.jobs.find_one({"job_id": job_id}, {'_id': 0})
        return doc or {"status": "unknown"}
    return JOBS.get(job_id, {"status": "unknown"})
