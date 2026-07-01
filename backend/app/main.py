from fastapi import FastAPI, File, UploadFile, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

from .models import Base, Resume, User, Job, Match
from .config import settings
from .worker import process_resume_file
from .openai_client import generate_feedback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = settings.database_url
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI(title="CV Coach", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

UPLOAD_DIR = '/tmp/uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)
Base.metadata.create_all(bind=engine)
logger.info("Database initialized")

@app.post('/api/upload-resume')
async def upload_resume(file: UploadFile = File(...), user_email: str = "user@example.com", background_tasks: BackgroundTasks = BackgroundTasks()):
    if not file:
        raise HTTPException(status_code=400, detail="No file")
    
    allowed = ('.pdf', '.doc', '.docx', '.txt', '.png', '.jpg', '.jpeg')
    if not file.filename.lower().endswith(allowed):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    try:
        timestamp = datetime.utcnow().timestamp()
        save_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{file.filename}")
        with open(save_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        session = SessionLocal()
        user = session.query(User).filter(User.email == user_email).first()
        if not user:
            user = User(email=user_email, name='User')
            session.add(user)
            session.commit()
        
        resume = Resume(user_id=user.id, s3_path=save_path, status='uploaded')
        session.add(resume)
        session.commit()
        resume_id = resume.id
        session.close()
        
        background_tasks.add_task(process_resume_file, resume_id, save_path)
        return {"resume_id": resume_id, "status": "queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/resume/{resume_id}')
def get_resume(resume_id: int):
    session = SessionLocal()
    resume = session.query(Resume).filter(Resume.id == resume_id).first()
    session.close()
    if not resume:
        raise HTTPException(status_code=404, detail='Not found')
    return {'id': resume.id, 'user_id': resume.user_id, 'status': resume.status, 'parsed': resume.parsed, 'created_at': resume.created_at.isoformat()}

@app.get('/api/resume/{resume_id}/matches')
def get_matches(resume_id: int, top: int = Query(10)):
    session = SessionLocal()
    resume = session.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        session.close()
        raise HTTPException(status_code=404, detail='Not found')
    
    if resume.status != 'parsed':
        session.close()
        return {'resume_id': resume_id, 'matches': []}
    
    parsed = resume.parsed or {}
    resume_skills = set()
    if isinstance(parsed.get('skills'), list):
        resume_skills = {s.get('name', '').lower() for s in parsed['skills'] if s.get('name')}
    
    all_jobs = session.query(Job).all()
    scored = []
    for job in all_jobs:
        job_raw = job.raw or {}
        job_desc = (job.description or "").lower()
        job_skills = set(s.lower() for s in job_raw.get('required_skills', []))
        matched = resume_skills.intersection(job_skills)
        skill_score = len(matched) / max(len(job_skills), 1) * 100 if job_skills else 50
        text_score = min(100, sum(1 for s in resume_skills if s in job_desc) * 15)
        composite = int((skill_score * 0.6 + text_score * 0.4))
        if composite > 30:
            scored.append({'job_id': job.id, 'job_title': job.title, 'company': job.company, 'location': job.location, 'score': composite, 'matched_skills': list(matched), 'explanation': f"Match: {len(matched)} skills"})
    
    scored.sort(key=lambda x: x['score'], reverse=True)
    session.close()
    return {'resume_id': resume_id, 'matches': scored[:top]}

@app.post('/api/resume/{resume_id}/improve')
def improve(resume_id: int, job_id: int = Query(...)):
    session = SessionLocal()
    resume = session.query(Resume).filter(Resume.id == resume_id).first()
    job = session.query(Job).filter(Job.id == job_id).first()
    session.close()
    if not resume or not job:
        raise HTTPException(status_code=404)
    feedback = generate_feedback(resume.parsed or {}, job.raw or {})
    return {'resume_id': resume_id, 'job_id': job_id, 'feedback': feedback}

@app.get('/api/health')
def health():
    return {'status': 'ok'}

@app.get('/')
def root():
    return {'name': 'CV Coach', 'version': '0.1.0', 'docs': '/docs'}
