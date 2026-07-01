import os
import logging
from .config import settings
from .openai_client import parse_resume_text, create_embeddings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, Resume
import pdfplumber
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)
DATABASE_URL = settings.database_url
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

def extract_text_from_pdf(path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        logger.warning(f"PDF extraction error: {e}")
    
    if text.strip():
        return text
    
    try:
        from pdf2image import convert_from_path
        pages = convert_from_path(path)
        for page in pages:
            ocr_text = pytesseract.image_to_string(page)
            if ocr_text:
                text += ocr_text + "\n"
    except Exception as e:
        logger.error(f"OCR fallback failed: {e}")
    return text

def extract_text_from_image(path: str) -> str:
    try:
        img = Image.open(path)
        return pytesseract.image_to_string(img)
    except Exception as e:
        logger.error(f"OCR error: {e}")
        return ""

def process_resume_file(resume_id: int, file_path: str):
    session = SessionLocal()
    resume = session.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        session.close()
        return

    try:
        resume.status = 'parsing'
        session.commit()
        
        if file_path.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
        elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            text = extract_text_from_image(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        
        text = text.strip()[:25000]
        if not text:
            resume.status = 'error'
            resume.parsed = {"error": "No text extracted"}
            session.commit()
            return
        
        parsed = parse_resume_text(text)
        resume.parsed = parsed
        resume.status = 'parsed' if not parsed.get('error') else 'error'
        session.commit()
        
        if not parsed.get('error'):
            try:
                create_embeddings([text])
            except:
                pass
    except Exception as e:
        logger.error(f"Error: {e}")
        resume.status = 'error'
        resume.parsed = {"error": str(e)}
        session.commit()
    finally:
        session.close()
