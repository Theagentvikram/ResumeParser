import os
import pdfplumber
import fitz  # PyMuPDF
import re

def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF file using PyMuPDF and fallback to pdfplumber if needed
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        String containing the extracted text
    """
    extracted_text = ""
    
    try:
        # Try with PyMuPDF first (faster)
        try:
            text_from_pymupdf = extract_with_pymupdf(file_path)
            if text_from_pymupdf and len(text_from_pymupdf.strip()) > 100:
                print("Successfully extracted text with PyMuPDF")
                extracted_text = text_from_pymupdf
            else:
                print("PyMuPDF extraction insufficient, trying pdfplumber...")
        except Exception as e:
            print(f"PyMuPDF extraction failed: {str(e)}")
        
        # If PyMuPDF didn't work well, try pdfplumber
        if len(extracted_text.strip()) < 100:
            try:
                text_from_pdfplumber = extract_with_pdfplumber(file_path)
                if text_from_pdfplumber and len(text_from_pdfplumber.strip()) > 100:
                    print("Successfully extracted text with pdfplumber")
                    if not extracted_text:
                        extracted_text = text_from_pdfplumber
                    else:
                        # Combine the results if both methods yielded some text
                        extracted_text = f"{extracted_text}\n\n{text_from_pdfplumber}"
                        print("Combined text from both extraction methods")
            except Exception as e:
                print(f"pdfplumber extraction failed: {str(e)}")
        
        # Clean and normalize the extracted text
        cleaned_text = clean_extracted_text(extracted_text)
        
        # Check if we got enough text to work with
        if cleaned_text and len(cleaned_text.strip()) > 100:
            return cleaned_text
        else:
            print("WARNING: Extracted very little usable text from PDF")
            return extracted_text  # Return what we have even if it's minimal
            
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        raise

def extract_with_pymupdf(file_path):
    """Extract text using PyMuPDF with enhanced handling"""
    text = ""
    try:
        doc = fitz.open(file_path)
        print(f"PDF document opened with PyMuPDF, {doc.page_count} pages found")
        
        for page_num, page in enumerate(doc):
            try:
                # Get text with more precise extraction to handle layouts better
                page_text = page.get_text("text")
                
                # Check if we have reasonable text content
                if len(page_text.strip()) < 10:
                    # Try with a different extraction method
                    page_text = page.get_text("blocks")
                    if isinstance(page_text, list):
                        page_text = "\n".join([block[4] for block in page_text if len(block) > 4])
                
                text += page_text + "\n\n"
                print(f"  - Page {page_num+1}: Extracted {len(page_text)} characters")
            except Exception as e:
                print(f"  - Error extracting page {page_num+1}: {str(e)}")
        
        doc.close()
        return text
    except Exception as e:
        print(f"PyMuPDF extraction error: {str(e)}")
        return ""

def extract_with_pdfplumber(file_path):
    """Extract text using pdfplumber with enhanced handling"""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            print(f"PDF document opened with pdfplumber, {len(pdf.pages)} pages found")
            
            for page_num, page in enumerate(pdf.pages):
                try:
                    # Standard text extraction
                    page_text = page.extract_text() or ""
                    
                    # If we got too little text, try to extract tables too
                    if len(page_text.strip()) < 50:
                        try:
                            tables = page.extract_tables()
                            if tables:
                                for table in tables:
                                    for row in table:
                                        page_text += " ".join([cell or "" for cell in row if cell]) + "\n"
                        except:
                            pass
                    
                    text += page_text + "\n\n"
                    print(f"  - Page {page_num+1}: Extracted {len(page_text)} characters")
                except Exception as e:
                    print(f"  - Error extracting page {page_num+1}: {str(e)}")
            
        return text
    except Exception as e:
        print(f"pdfplumber extraction error: {str(e)}")
        return ""

def clean_extracted_text(text):
    """Clean up the extracted text to improve analysis results"""
    if not text:
        return ""
        
    # Replace multiple newlines with a single newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r' {2,}', ' ', text)
    
    # Remove odd characters that might affect analysis
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    
    # Replace tab characters with spaces
    text = text.replace('\t', ' ')
    
    # Remove page numbers and headers/footers (common patterns)
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)  # Standalone page numbers
    text = re.sub(r'\n\s*Page \d+ of \d+\s*\n', '\n', text)  # "Page X of Y" patterns
    
    # Remove email and phone headers but keep the values
    text = re.sub(r'(?i)email\s*:\s*', '', text)
    text = re.sub(r'(?i)phone\s*:\s*', '', text)
    text = re.sub(r'(?i)tel\s*:\s*', '', text)
    
    # Remove repetitive copyright or confidential footers
    text = re.sub(r'(?i)confidential.*?resume', '', text)
    text = re.sub(r'(?i)copyright.*?\d{4}', '', text)
    
    # Fix spacing around common punctuation
    text = re.sub(r'\s+,', ',', text)
    text = re.sub(r'\s+\.', '.', text)
    
    # Remove form field indicators often found in PDFs
    text = re.sub(r'\[.*?\]', '', text)
    
    # Attempt to identify and enhance section headers
    text = re.sub(r'(\n[A-Z][A-Z\s]{3,})\s*', r'\n\n\1\n', text)
    
    # Detect and clean bullet points for better formatting
    text = re.sub(r'•', '- ', text)
    text = re.sub(r'[\*\+→●■◆➢]', '- ', text)
    
    # Fix spacing issues with bullet points
    text = re.sub(r'(\n\s*)-\s+', r'\1- ', text)
    
    # Remove excessive whitespace at beginning/end
    return text.strip() 