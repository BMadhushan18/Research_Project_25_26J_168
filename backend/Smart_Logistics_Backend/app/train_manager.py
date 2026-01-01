import os
from uuid import uuid4
from typing import Dict
from fastapi import BackgroundTasks
from datetime import datetime

from app.db import get_db, is_available

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))

# Fallback in-memory store for environments without MongoDB
JOBS: Dict[str, dict] = {}


def run_training(file_path: str, out_dir: str = MODELS_DIR):
    """Run training synchronously using existing scripts/train.py utilities."""
    # Import here to avoid import cycles at module import time in tests
    from scripts.train import load_df, fit_and_save
    df = load_df(file_path)
    fit_and_save(df, out_dir)


def _runner(job_id: str, file_path: str, out_dir: str):
    db = get_db()
    try:
        if db:
            db.jobs.update_one({"job_id": job_id}, {"$set": {"status": "running", "started_at": datetime.utcnow()}}, upsert=True)
        else:
            JOBS[job_id] = {"status": "running"}

        run_training(file_path, out_dir)

        # Record completion and basic model metadata
        metadata = {"artifacts": os.listdir(out_dir), "completed_at": datetime.utcnow()}
        if db:
            db.jobs.update_one({"job_id": job_id}, {"$set": {"status": "completed", "metadata": metadata}}, upsert=True)
            db.models.insert_one({"job_id": job_id, "metadata": metadata, "created_at": datetime.utcnow()})
        else:
            JOBS[job_id] = {"status": "completed", "metadata": metadata}
    except Exception as e:
        if db:
            db.jobs.update_one({"job_id": job_id}, {"$set": {"status": "failed", "error": str(e), "failed_at": datetime.utcnow()}}, upsert=True)
        else:
            JOBS[job_id] = {"status": "failed", "error": str(e)}


def start_background_job(file_path: str, out_dir: str = MODELS_DIR, bg_tasks: BackgroundTasks = None) -> str:
    job_id = uuid4().hex
    db = get_db()
    if db:
        db.jobs.insert_one({"job_id": job_id, "status": "queued", "file_path": file_path, "created_at": datetime.utcnow()})
    else:
        JOBS[job_id] = {"status": "queued", "file_path": file_path}

    if bg_tasks:
        bg_tasks.add_task(_runner, job_id, file_path, out_dir)
    else:
        # fallback: run inline
        _runner(job_id, file_path, out_dir)
    return job_id


def get_job(job_id: str):
    db = get_db()
    if db:
        doc = db.jobs.find_one({"job_id": job_id}, {'_id': 0})
        return doc or {"status": "unknown"}
    return JOBS.get(job_id, {"status": "unknown"})
