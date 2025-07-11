import json
import logging
from typing import List
from pathlib import Path
from datetime import datetime

from app.services.ranker import rank_resumes
from app.services.parser import parse_resume
from app.services.status import update_job_status
from app.utils.pdf_utils import extract_text_from_pdf
from app.services.embedding import generate_embeddings
from app.db.models import JobResult, ResumeResult, db_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                    "original_name": Path(file_path).name,
                    "text_content": text_content
                })
                
                # Update progress
                progress = 20 + (i + 1) * 20 // len(file_paths)
                update_job_status(job_id, "processing", progress, f"Extracted text from {i+1}/{len(file_paths)} files")
                
            except Exception as e:
                logger.error(f"Error extracting text from {file_path}: {str(e)}")
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
                logger.info(f"Parsed data for {resume['filename']}: {parsed_data}")
                
                
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
