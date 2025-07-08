import PyPDF2
import fitz  # PyMuPDF
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

async def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """
    Extract text from PDF file using PyMuPDF (fallback to PyPDF2)
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text content or None if extraction fails
    """
    try:
        # Try PyMuPDF first (better text extraction)
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        
        if text.strip():
            return text.strip()
        
        # Fallback to PyPDF2
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        
        return text.strip() if text.strip() else None
        
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        return None