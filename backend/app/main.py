from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
import uuid
import asyncio
from pathlib import Path
import logging
from datetime import datetime

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILES = 10

# Ensure upload directory exists
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

async def process_resumes_async(job_id: str, file_paths: List[str], job_description: str):
    """Process resumes asynchronously (placeholder for actual processing)"""
    try:
        # This is where you would integrate with your resume processing services
        # For now, we'll just log the processing
        logger.info(f"Starting processing for job {job_id}")
        logger.info(f"Files to process: {len(file_paths)}")
        logger.info(f"Job description length: {len(job_description)} characters")
        
        # Simulate processing time
        await asyncio.sleep(1)
        
        # Here you would typically:
        # 1. Extract text from PDFs using pdf_utils
        # 2. Parse resumes using parser service
        # 3. Generate embeddings using embedding service
        # 4. Rank resumes using ranker service
        # 5. Store results in database
        
        logger.info(f"Processing completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error processing resumes for job {job_id}: {str(e)}")
        raise

@app.post("/api/upload-resumes")
async def upload_resumes(
    resumes: List[UploadFile] = File(...),
    job_description: str = Form(...),
):
    """
    Upload multiple resume PDFs and job description for ranking
    
    Args:
        resumes: List of PDF files (max 10 files, max 10MB each)
        job_description: Job description text
    
    Returns:
        JSON response with job_id and processing status
    """
    try:
        # Validate input
        if not resumes:
            raise HTTPException(status_code=400, detail="No resume files provided")
        
        if len(resumes) > MAX_FILES:
            raise HTTPException(
                status_code=400, 
                detail=f"Too many files. Maximum {MAX_FILES} files allowed"
            )
        
        if not job_description or len(job_description.strip()) < 10:
            raise HTTPException(
                status_code=400, 
                detail="Job description must be at least 10 characters long"
            )
        
        # Validate each file
        for file in resumes:
            if not validate_file(file):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file: {file.filename}. Only PDF files are allowed."
                )
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Save files
        saved_files = []
        failed_files = []
        
        for file in resumes:
            try:
                file_path = await save_file(file, job_id)
                saved_files.append({
                    "original_name": file.filename,
                    "file_path": file_path,
                    "size": len(await file.read()) if hasattr(file, 'read') else 0
                })
                # Reset file pointer for next operations
                await file.seek(0)
            except Exception as e:
                failed_files.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        # Check if any files were saved successfully
        if not saved_files:
            raise HTTPException(
                status_code=400,
                detail="No files could be processed successfully"
            )
        
        # Start async processing
        file_paths = [f["file_path"] for f in saved_files]
        
        # In a real application, you might want to use Celery or similar for background processing
        # For now, we'll start the processing without waiting for it to complete
        asyncio.create_task(process_resumes_async(job_id, file_paths, job_description))
        
        # Prepare response
        response_data = {
            "job_id": job_id,
            "status": "processing",
            "message": "Files uploaded successfully. Processing started.",
            "files_processed": len(saved_files),
            "files_failed": len(failed_files),
            "processed_files": saved_files,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if failed_files:
            response_data["failed_files"] = failed_files
        
        logger.info(f"Upload completed for job {job_id}. {len(saved_files)} files processed successfully.")
        
        return JSONResponse(
            status_code=202,  # Accepted for processing
            content=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload_resumes: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status of a resume processing job
    
    Args:
        job_id: Unique job identifier
    
    Returns:
        JSON response with job status
    """
    try:
        # In a real application, you would check the database or cache for job status
        # For now, we'll return a mock response
        
        # Check if job directory exists
        job_dir = UPLOAD_DIR / job_id
        if not job_dir.exists():
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Mock status response
        return {
            "job_id": job_id,
            "status": "completed",  # Could be: processing, completed, failed
            "progress": 100,
            "message": "Resume processing completed successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/job/{job_id}")
async def cleanup_job(job_id: str):
    """
    Clean up job files and data
    
    Args:
        job_id: Unique job identifier
    
    Returns:
        JSON response confirming cleanup
    """
    try:
        job_dir = UPLOAD_DIR / job_id
        
        if job_dir.exists():
            # Remove all files in the job directory
            for file_path in job_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()
            
            # Remove the directory
            job_dir.rmdir()
            
            logger.info(f"Cleaned up job {job_id}")
            
            return {
                "job_id": job_id,
                "status": "cleaned",
                "message": "Job files cleaned up successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Job not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "upload_dir": str(UPLOAD_DIR.absolute()),
        "max_files": MAX_FILES,
        "max_file_size_mb": MAX_FILE_SIZE / 1024 / 1024
    }