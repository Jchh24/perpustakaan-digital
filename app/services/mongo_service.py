import os
import json
from datetime import datetime, timezone
from typing import Optional

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "perpustakaan_digital")
FALLBACK_LOG_PATH = "./data/activity_logs.jsonl"

mongo_client = None
mongo_collection = None

try:
    from pymongo import MongoClient
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    client.server_info()
    mongo_client = client
    mongo_collection = mongo_client[MONGO_DB_NAME]["activity_logs"]
except Exception:
    mongo_client = None
    mongo_collection = None

def log_activity(action: str, username: str = "anonymous", role: str = "guest", user_id: Optional[str] = None, ip_address: str = "", details: dict = None):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "username": username,
        "role": role,
        "user_id": user_id,
        "ip_address": ip_address,
        "details": details or {}
    }
    if mongo_collection is not None:
        try:
            mongo_collection.insert_one(entry)
            return
        except Exception:
            pass
    try:
        os.makedirs(os.path.dirname(FALLBACK_LOG_PATH), exist_ok=True)
        with open(FALLBACK_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

def get_recent_logs(limit: int = 50):
    if mongo_collection is not None:
        try:
            records = list(mongo_collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
            return records
        except Exception:
            pass
    logs = []
    if os.path.exists(FALLBACK_LOG_PATH):
        try:
            with open(FALLBACK_LOG_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in reversed(lines[-limit:]):
                    line = line.strip()
                    if line:
                        logs.append(json.loads(line))
        except Exception:
            pass
    return logs
