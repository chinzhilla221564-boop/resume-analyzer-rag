"""
PDF Text Extraction Module
Extracts text from uploaded PDF and text files
"""
import PyPDF2
from pathlib import Path
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handle PDF and text file processing"""
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> Optional[str]:
        """
        Extract text from PDF file
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text or None if error
        """
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {page_num} ---\n"
                        text += page_text
                    
            logger.info(f"Successfully extracted {len(text)} characters from {file_path}")
            return text if text.strip() else None
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return None
    
    @staticmethod
    def extract_text_from_txt(file_path: str) -> Optional[str]:
        """
        Extract text from text file
        
        Args:
            file_path: Path to the text file
            
        Returns:
            Extracted text or None if error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            logger.info(f"Successfully extracted {len(text)} characters from {file_path}")
            return text if text.strip() else None
            
        except Exception as e:
            logger.error(f"Error extracting text from text file: {str(e)}")
            return None
    
    @staticmethod
    def extract_text(file_path: str) -> Optional[str]:
        """
        Extract text based on file extension
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extracted text or None if error
        """
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.pdf':
            return PDFProcessor.extract_text_from_pdf(str(file_path))
        elif file_path.suffix.lower() == '.txt':
            return PDFProcessor.extract_text_from_txt(str(file_path))
        else:
            logger.error(f"Unsupported file type: {file_path.suffix}")
            return None
    
    @staticmethod
    def save_uploaded_file(uploaded_file, save_path: str) -> bool:
        """
        Save uploaded file to disk
        
        Args:
            uploaded_file: Streamlit uploaded file object
            save_path: Path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(save_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            logger.info(f"File saved to {save_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            return False


# Test the module
if __name__ == "__main__":
    # Test extraction
    processor = PDFProcessor()
    print("PDF Processor module loaded successfully")