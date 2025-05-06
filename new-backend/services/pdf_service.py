"""
PDF service for extracting text from resume PDFs
"""
import fitz  # PyMuPDF
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF file using PyMuPDF
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text as a string
    """
    try:
        logger.info(f"Extracting text from PDF: {file_path}")
        
        # Open the PDF
        doc = fitz.open(file_path)
        
        # Extract text from each page
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        
        # Close the document
        doc.close()
        
        logger.info(f"Extracted {len(text)} characters from PDF")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise Exception(f"Failed to extract text from PDF: {str(e)}")
