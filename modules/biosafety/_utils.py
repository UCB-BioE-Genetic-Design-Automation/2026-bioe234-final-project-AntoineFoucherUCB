"""Utilities like RAG markdown conversion
"""

import os
import logging

def convert_to_markdown(file_path: str) -> str:
    """
    Reads a document of various types and converts its text to Markdown.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Document not found at path: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext in ['.txt', '.md', '.json', '.csv']:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        elif ext == '.pdf':
            # Requires: pip install pymupdf
            import fitz 
            text = f"## Document: {os.path.basename(file_path)}\n\n"
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text() + "\n\n"
            return text
            
        elif ext == '.docx':
            # Requires: pip install python-docx
            import docx
            doc = docx.Document(file_path)
            text = f"## Document: {os.path.basename(file_path)}\n\n"
            for para in doc.paragraphs:
                text += para.text + "\n\n"
            return text
            
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
            
    except ImportError as e:
        logging.error(f"Missing library for parsing {ext} files: {e}")
        return f"Error: Missing required library to parse {ext} files. Please install it."
    except Exception as e:
        logging.error(f"Error parsing document: {e}")
        raise
