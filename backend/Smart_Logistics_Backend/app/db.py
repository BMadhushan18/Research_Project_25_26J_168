import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from typing import Optional
from dotenv import load_dotenv

# Load .env if present (local development convenience)
load_dotenv()

# Read connection details from environment for safety
# Set MONGODB_URI in your environment or in a .env file:
# MONGODB_URI="mongodb+srv://<user>:<password>@cluster0.xx78u5w.mongodb.net/?appName=Cluster0"
MONGODB_URI = os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URI')

_client: Optional[MongoClient] = None
_db = None


def get_client(timeout_ms: int = 5000) -> Optional[MongoClient]:
    global _client
    if _client is None:
        if not MONGODB_URI:
            return None
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=timeout_ms)
        try:
            # attempt a quick server selection
            _client.server_info()
        except ServerSelectionTimeoutError:
            # connection failed - leave client but it may raise during operations
            pass
    return _client


def get_db():
    global _db
    if _db is None:
        client = get_client()
        if client is None:
            return None
        _db = client.get_database('smart_logistics')
    return _db


def is_available() -> bool:
    client = get_client()
    if client is None:
        return False
    try:
        client.admin.command('ping')
        return True
    except Exception:
        return False
