import uuid
import logging
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILES = 10

UPLOAD_DIR.mkdir(exist_ok=True)

def validate_file(file: UploadFile) -> bool:
    """Validate uploaded file"""
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False
    
    # Check file size (this is approximate, actual size check happens during read)
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        return False
    
    return True

async def save_file(file: UploadFile, job_id: str) -> str:
    """Save uploaded file to disk"""
    try:
        # Generate unique filename
        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        # Create job-specific directory
        job_dir = UPLOAD_DIR / job_id
        job_dir.mkdir(exist_ok=True)
        
        file_path = job_dir / unique_filename
        
        # Read and save file
        content = await file.read()
        
        # Check actual file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File {file.filename} is too large. Maximum size is {MAX_FILE_SIZE/1024/1024}MB"
            )
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved file: {file.filename} -> {file_path}")
        return str(file_path)
        
    except Exception as e:
        logger.error(f"Error saving file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
