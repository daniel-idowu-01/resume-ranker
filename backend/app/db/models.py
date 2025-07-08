from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import os
from contextlib import contextmanager

Base = declarative_base()

class JobResult(Base):
    __tablename__ = "job_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), unique=True, index=True, nullable=False)
    job_description = Column(Text, nullable=False)
    total_resumes = Column(Integer, default=0)
    processed_resumes = Column(Integer, default=0)
    status = Column(String(50), default="processing")  # processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to resume results
    resume_results = relationship("ResumeResult", back_populates="job_result", cascade="all, delete-orphan")

class ResumeResult(Base):
    __tablename__ = "resume_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_result_id = Column(Integer, ForeignKey("job_results.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    text_content = Column(Text)
    parsed_data = Column(JSON)  # Store parsed resume data as JSON
    similarity_score = Column(Float, default=0.0)
    rank = Column(Integer, default=0)
    embedding = Column(JSON)  # Store embedding vector as JSON array
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to job result
    job_result = relationship("JobResult", back_populates="resume_results")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resume_ranking.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

@contextmanager
def db_session():
    """Context manager for database sessions"""
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()