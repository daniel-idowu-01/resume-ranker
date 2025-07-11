from datetime import datetime
from typing import List, Optional, Dict, Any

# In-memory job status storage (replace with Redis/Database in production)
job_status_store = {}

def update_job_status(job_id: str, status: str, progress: int = 0, message: str = "", data: Dict[str, Any] = None):
    """Update job status in memory store"""
    job_status_store[job_id] = {
        "status": status,
        "progress": progress,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data or {}
    }
