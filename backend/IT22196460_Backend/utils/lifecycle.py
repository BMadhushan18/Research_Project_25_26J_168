"""
App lifecycle events — model loading happens here so it's done once
at startup, not on every request.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

from services.model_service import load_models

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Loading ML models...")
    load_models()
    logger.info("✅ Models ready.")
    yield
    # Shutdown (nothing to clean up for joblib models)
    logger.info("👋 Shutting down.")
