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
from app.utils.pdf_utils import extract_text_from_pdf
from app.services.parser import parse_resume
from app.services.embedding import generate_embeddings
from app.services.ranker import rank_resumes
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

# In-memory job status storage (replace with Redis/Database in production)
job_status_store = {}

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

def update_job_status(job_id: str, status: str, progress: int = 0, message: str = "", data: Dict[str, Any] = None):
    """Update job status in memory store"""
    job_status_store[job_id] = {
        "status": status,
        "progress": progress,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data or {}
    }

async def process_resumes_async(job_id: str, file_paths: List[str], job_description: str):
    """Process resumes asynchronously with full service integration"""
    try:
        update_job_status(job_id, "processing", 0, "Starting resume processing...")
        
        logger.info(f"Starting processing for job {job_id}")
        logger.info(f"Files to process: {len(file_paths)}")
        logger.info(f"Job description length: {len(job_description)} characters")
        
        # Step 1: Extract text from PDFs
        update_job_status(job_id, "processing", 20, "Extracting text from PDFs...")
        
        extracted_resumes = []
        for i, file_path in enumerate(file_paths):
            try:
                logger.info(f"Processing file {i+1}/{len(file_paths)}: {file_path}")
                
                # Extract text from PDF
                text_content = await extract_text_from_pdf(file_path)
                
                if not text_content or len(text_content.strip()) < 50:
                    logger.warning(f"Minimal or no text extracted from {file_path}")
                    continue
                
                extracted_resumes.append({
                    "file_path": file_path,
                    "filename": Path(file_path).name,
                    "original_name": Path(file_path).name,  # You might want to store original names
                    "text_content": text_content
                })
                
                # Update progress
                progress = 20 + (i + 1) * 20 // len(file_paths)
                update_job_status(job_id, "processing", progress, f"Extracted text from {i+1}/{len(file_paths)} files")
                
            except Exception as e:
                logger.error(f"Error extracting text from {file_path}: {str(e)}")
                # Continue processing other files
                continue
        
        if not extracted_resumes:
            update_job_status(job_id, "failed", 0, "No text could be extracted from any resume")
            return
        
        # Step 2: Parse resumes
        update_job_status(job_id, "processing", 40, "Parsing resume data...")
        
        parsed_resumes = []
        for i, resume in enumerate(extracted_resumes):
            try:
                logger.info(f"Parsing resume {i+1}/{len(extracted_resumes)}: {resume['filename']}")
                
                # Parse resume to extract structured data
                parsed_data = await parse_resume(resume['text_content'])
                
                parsed_resumes.append({
                    **resume,
                    "parsed_data": parsed_data
                })
                
                # Update progress
                progress = 40 + (i + 1) * 20 // len(extracted_resumes)
                update_job_status(job_id, "processing", progress, f"Parsed {i+1}/{len(extracted_resumes)} resumes")
                
            except Exception as e:
                logger.error(f"Error parsing resume {resume['filename']}: {str(e)}")
                # Continue with basic text content
                parsed_resumes.append({
                    **resume,
                    "parsed_data": {"error": str(e)}
                })
        
        # Step 3: Generate embeddings
        update_job_status(job_id, "processing", 60, "Generating embeddings...")
        
        try:
            logger.info("Generating embeddings for resumes and job description")
            
            # Prepare texts for embedding
            resume_texts = [resume['text_content'] for resume in parsed_resumes]
            all_texts = resume_texts + [job_description]
            
            # Generate embeddings for all texts
            embeddings = await generate_embeddings(all_texts)
            
            # Split embeddings
            resume_embeddings = embeddings[:-1]
            job_embedding = embeddings[-1]
            
            # Add embeddings to resume data
            for i, resume in enumerate(parsed_resumes):
                resume['embedding'] = resume_embeddings[i]
            
            update_job_status(job_id, "processing", 80, "Generated embeddings for all resumes")
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            update_job_status(job_id, "failed", 0, f"Failed to generate embeddings: {str(e)}")
            return
        
        # Step 4: Rank resumes
        update_job_status(job_id, "processing", 90, "Ranking resumes...")
        
        try:
            logger.info("Ranking resumes against job description")
            
            # Rank resumes based on similarity to job description
            ranking_results = await rank_resumes(
                resumes=parsed_resumes,
                job_description=job_description,
                job_embedding=job_embedding
            )
            
            update_job_status(job_id, "processing", 95, "Completed ranking resumes")
            
        except Exception as e:
            logger.error(f"Error ranking resumes: {str(e)}")
            update_job_status(job_id, "failed", 0, f"Failed to rank resumes: {str(e)}")
            return
        
        # Step 5: Store results in database
        update_job_status(job_id, "processing", 98, "Storing results in database...")
        
        try:
            with db_session() as session:
                # Create job result record
                job_result = JobResult(
                    job_id=job_id,
                    job_description=job_description,
                    total_resumes=len(parsed_resumes),
                    processed_resumes=len(ranking_results),
                    status="completed",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(job_result)
                session.flush()  # Get the ID
                
                # Store individual resume results
                for i, result in enumerate(ranking_results):
                    resume_result = ResumeResult(
                        job_result_id=job_result.id,
                        filename=result['filename'],
                        original_name=result.get('original_name', result['filename']),
                        file_path=result['file_path'],
                        text_content=result['text_content'],
                        parsed_data=json.dumps(result.get('parsed_data', {})),
                        similarity_score=result.get('similarity_score', 0.0),
                        rank=i + 1,
                        embedding=result.get('embedding', []),
                        created_at=datetime.utcnow()
                    )
                    session.add(resume_result)
                
                session.commit()
                logger.info(f"Stored results for job {job_id} in database")
        
        except Exception as e:
            logger.error(f"Error storing results in database: {str(e)}")
            # Don't fail the entire process if DB storage fails
            logger.warning("Continuing without database storage")
        
        # Step 6: Complete processing
        final_results = {
            "job_id": job_id,
            "total_resumes": len(file_paths),
            "processed_resumes": len(ranking_results),
            "top_candidates": ranking_results[:5],  # Top 5 candidates
            "processing_summary": {
                "extracted": len(extracted_resumes),
                "parsed": len(parsed_resumes),
                "ranked": len(ranking_results)
            }
        }
        
        update_job_status(
            job_id, 
            "completed", 
            100, 
            f"Successfully processed {len(ranking_results)} resumes",
            final_results
        )
        
        logger.info(f"Processing completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error processing resumes for job {job_id}: {str(e)}")
        update_job_status(job_id, "failed", 0, f"Processing failed: {str(e)}")
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