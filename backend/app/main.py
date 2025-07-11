from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import os
import uuid
import asyncio
from pathlib import Path
import logging
from datetime import datetime
import json

# Import your services
from app.services.uploader import validate_file, save_file
from app.services.processor import process_resumes_async
from app.services.status import update_job_status, job_status_store
from app.db.models import JobResult, ResumeResult, db_session

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
        
        # Initialize job status
        update_job_status(job_id, "uploading", 0, "Saving uploaded files...")
        
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
            update_job_status(job_id, "failed", 0, "No files could be processed successfully")
            raise HTTPException(
                status_code=400,
                detail="No files could be processed successfully"
            )
        
        # Start async processing
        file_paths = [f["file_path"] for f in saved_files]
        
        # Start background processing
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

@app.get("/api/job-status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status of a resume processing job
    
    Args:
        job_id: Unique job identifier
    
    Returns:
        JSON response with job status and results
    """
    try:
        # Check in-memory status first
        if job_id in job_status_store:
            status_data = job_status_store[job_id]
            return {
                "job_id": job_id,
                **status_data
            }
        
        # Check if job directory exists
        job_dir = UPLOAD_DIR / job_id
        if not job_dir.exists():
            raise HTTPException(status_code=404, detail="Job not found")
        
        # If no status in memory, check database
        try:
            with db_session() as session:
                job_result = session.query(JobResult).filter(JobResult.job_id == job_id).first()
                if job_result:
                    resume_results = session.query(ResumeResult).filter(
                        ResumeResult.job_result_id == job_result.id
                    ).order_by(ResumeResult.rank).all()
                    
                    return {
                        "job_id": job_id,
                        "status": job_result.status,
                        "progress": 100 if job_result.status == "completed" else 0,
                        "message": "Processing completed",
                        "timestamp": job_result.updated_at.isoformat(),
                        "data": {
                            "total_resumes": job_result.total_resumes,
                            "processed_resumes": job_result.processed_resumes,
                            "top_candidates": [
                                {
                                    "filename": r.filename,
                                    "similarity_score": r.similarity_score,
                                    "rank": r.rank,
                                    "parsed_data": json.loads(r.parsed_data) if r.parsed_data else {}
                                }
                                for r in resume_results[:5]
                            ]
                        }
                    }
        except Exception as e:
            logger.error(f"Error querying database for job {job_id}: {str(e)}")
        
        # Default response if job exists but no status found
        return {
            "job_id": job_id,
            "status": "unknown",
            "progress": 0,
            "message": "Job found but status unknown",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/job-results/{job_id}")
async def get_job_results(job_id: str):
    """
    Get detailed results for a completed job
    
    Args:
        job_id: Unique job identifier
    
    Returns:
        JSON response with detailed results
    """
    try:
        with db_session() as session:
            job_result = session.query(JobResult).filter(JobResult.job_id == job_id).first()
            
            if not job_result:
                raise HTTPException(status_code=404, detail="Job not found")
            
            if job_result.status != "completed":
                raise HTTPException(status_code=400, detail="Job not completed yet")
            
            resume_results = session.query(ResumeResult).filter(
                ResumeResult.job_result_id == job_result.id
            ).order_by(ResumeResult.rank).all()
            
            return {
                "job_id": job_id,
                "job_description": job_result.job_description,
                "total_resumes": job_result.total_resumes,
                "processed_resumes": job_result.processed_resumes,
                "created_at": job_result.created_at.isoformat(),
                "updated_at": job_result.updated_at.isoformat(),
                "results": [
                    {
                        "filename": r.filename,
                        "original_name": r.original_name,
                        "similarity_score": r.similarity_score,
                        "rank": r.rank,
                        "parsed_data": json.loads(r.parsed_data) if r.parsed_data else {},
                        "text_preview": r.text_content[:500] + "..." if len(r.text_content) > 500 else r.text_content
                    }
                    for r in resume_results
                ]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job results for {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/job/{job_id}")
async def cleanup_job(job_id: str):
    """
    Clean up job files and data
    
    Args:
        job_id: Unique job identifier
    
    Returns:
        JSON response confirming cleanup
    """
    try:
        # Clean up files
        job_dir = UPLOAD_DIR / job_id
        if job_dir.exists():
            # Remove all files in the job directory
            for file_path in job_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()
            
            # Remove the directory
            job_dir.rmdir()
            
            logger.info(f"Cleaned up files for job {job_id}")
        
        # Clean up in-memory status
        if job_id in job_status_store:
            del job_status_store[job_id]
        
        # Clean up database records
        try:
            with db_session() as session:
                job_result = session.query(JobResult).filter(JobResult.job_id == job_id).first()
                if job_result:
                    # Delete related resume results first
                    session.query(ResumeResult).filter(
                        ResumeResult.job_result_id == job_result.id
                    ).delete()
                    
                    # Delete job result
                    session.delete(job_result)
                    session.commit()
                    
                    logger.info(f"Cleaned up database records for job {job_id}")
        except Exception as e:
            logger.error(f"Error cleaning up database for job {job_id}: {str(e)}")
        
        return {
            "job_id": job_id,
            "status": "cleaned",
            "message": "Job files and data cleaned up successfully"
        }
            
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
        "max_file_size_mb": MAX_FILE_SIZE / 1024 / 1024,
        "active_jobs": len(job_status_store)
    }