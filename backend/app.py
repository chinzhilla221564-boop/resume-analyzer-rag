from fastapi import FastAPI, UploadFile, File, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import tempfile
import os
from pathlib import Path
import PyPDF2
import docx
import jwt
from datetime import datetime, timedelta
from typing import Optional
from backend.database import load_users, save_users, hash_password, init_db

app = FastAPI()

# Initialize database
init_db()

# ============================================
# FORCE CORS HEADERS ON EVERY RESPONSE
# ============================================
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "https://chinzhilla221564-boop.github.io"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept"
    return response

# Handle OPTIONS requests directly
@app.options("/{path:path}")
async def options_handler(path: str):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "https://chinzhilla221564-boop.github.io",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
        }
    )

# ============================================
# HEALTH & ROOT ROUTES
# ============================================

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.get("/")
async def root():
    return {"message": "AI Resume Analyzer API", "status": "running"}

# Secret key for JWT
SECRET_KEY = "your-secret-key-resume-ai-2025"
ALGORITHM = "HS256"

# ============================================
# STATIC FILES MOUNTING
# ============================================
frontend_path = Path(__file__).parent.parent / "frontend"
css_path = frontend_path / "css"
js_path = frontend_path / "js"

css_path.mkdir(parents=True, exist_ok=True)
js_path.mkdir(parents=True, exist_ok=True)

app.mount("/css", StaticFiles(directory=str(css_path)), name="css")
app.mount("/js", StaticFiles(directory=str(js_path)), name="js")

print(f"✅ CSS mounted from: {css_path}")
print(f"✅ JS mounted from: {js_path}")

# ============================================
# USER DATABASE (Persistent)
# ============================================

class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_token(email: str) -> str:
    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("email")
    except:
        return None

# ============================================
# AUTHENTICATION ROUTES
# ============================================

@app.post("/api/auth/register")
async def register(user: UserRegister):
    users = load_users()
    
    if user.email in users:
        raise HTTPException(400, "Email already registered")
    
    users[user.email] = {
        "name": user.name,
        "email": user.email,
        "password": hash_password(user.password),
        "created_at": datetime.now().isoformat(),
        "resume_history": []
    }
    
    save_users(users)
    token = create_token(user.email)
    
    return JSONResponse(content={
        "success": True,
        "message": "Registration successful!",
        "token": token,
        "user": {
            "name": user.name,
            "email": user.email
        }
    })

@app.post("/api/auth/login")
async def login(user: UserLogin):
    users = load_users()
    
    if user.email not in users:
        raise HTTPException(400, "Invalid email or password")
    
    if not verify_password(user.password, users[user.email]["password"]):
        raise HTTPException(400, "Invalid email or password")
    
    token = create_token(user.email)
    
    return JSONResponse(content={
        "success": True,
        "message": "Login successful!",
        "token": token,
        "user": {
            "name": users[user.email]["name"],
            "email": user.email
        }
    })

@app.post("/api/auth/logout")
async def logout():
    return {"success": True, "message": "Logged out successfully"}

@app.get("/api/auth/verify")
async def verify(token: str):
    users = load_users()
    email = verify_token(token)
    if not email or email not in users:
        raise HTTPException(401, "Invalid token")
    
    return {
        "valid": True,
        "user": {
            "name": users[email]["name"],
            "email": email
        }
    }

# ============================================
# RESUME STORAGE (Persistent per user)
# ============================================
resume_data = {}

class JobDesc(BaseModel):
    job_description: str
    token: str

def extract_text_from_file(file_path, file_extension):
    text = ""
    
    if file_extension == '.pdf':
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    
    elif file_extension == '.docx':
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    
    else:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    
    return text

@app.post("/api/upload")
async def upload(file: UploadFile = File(...), token: str = None):
    if not token:
        raise HTTPException(401, "Authentication required")
    
    email = verify_token(token)
    if not email:
        raise HTTPException(401, "Invalid token")
    
    content = await file.read()
    file_extension = Path(file.filename).suffix.lower()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        extracted_text = extract_text_from_file(tmp_path, file_extension)
        
        if email not in resume_data:
            resume_data[email] = {}
        resume_data[email]["text"] = extracted_text
        resume_data[email]["filename"] = file.filename
        
    except Exception as e:
        resume_data[email] = {"text": f"Content from {file.filename}", "filename": file.filename}
    finally:
        os.unlink(tmp_path)
    
    return {
        "message": f"✅ {file.filename} uploaded successfully!",
        "filename": file.filename,
        "text_length": len(extracted_text) if extracted_text else 0,
        "word_count": len(extracted_text.split()) if extracted_text else 0
    }

@app.post("/api/analyze")
async def analyze(req: JobDesc):
    email = verify_token(req.token)
    if not email:
        raise HTTPException(401, "Invalid token")
    
    if email not in resume_data or not resume_data[email].get("text"):
        raise HTTPException(400, "No resume loaded. Please upload a resume first.")
    
    resume_text = resume_data[email]["text"]
    resume_filename = resume_data[email]["filename"]
    job_lower = req.job_description.lower()
    resume_lower = resume_text.lower()
    
    keywords = {
        "💻 Languages": ['python', 'java', 'javascript', 'typescript', 'go', 'rust', 'swift', 'kotlin', 'c++', 'c#', 'ruby', 'php', 'scala', 'r'],
        "🌐 Web": ['react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'spring', 'html', 'css', 'bootstrap', 'tailwind'],
        "🗄️ Databases": ['sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'redis', 'cassandra', 'dynamodb'],
        "☁️ Cloud": ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'github actions', 'terraform'],
        "🤝 Soft Skills": ['leadership', 'communication', 'problem solving', 'teamwork', 'agile', 'scrum', 'mentoring'],
        "🛠️ Tools": ['git', 'github', 'gitlab', 'jira', 'confluence', 'postman', 'figma']
    }
    
    category_results = {}
    all_missing = []
    total_matched = 0
    total_keywords = 0
    
    for category, kw_list in keywords.items():
        category_matched = []
        category_missing = []
        
        for kw in kw_list:
            if kw in job_lower:
                total_keywords += 1
                if kw in resume_lower:
                    category_matched.append(kw)
                    total_matched += 1
                else:
                    category_missing.append(kw)
                    all_missing.append(kw)
        
        if category_matched or category_missing:
            category_results[category] = {
                "matched": category_matched,
                "missing": category_missing,
                "match_count": len(category_matched),
                "total_relevant": len(category_matched) + len(category_missing)
            }
    
    score = int((total_matched / total_keywords) * 100) if total_keywords > 0 else 50
    
    users = load_users()
    if email in users:
        history_entry = {
            "date": datetime.now().isoformat(),
            "score": score,
            "job_title": req.job_description[:50],
            "missing_count": len(all_missing)
        }
        if "resume_history" not in users[email]:
            users[email]["resume_history"] = []
        users[email]["resume_history"].insert(0, history_entry)
        if len(users[email]["resume_history"]) > 10:
            users[email]["resume_history"] = users[email]["resume_history"][:10]
        save_users(users)
    
    # HTML analysis (shortened for brevity - keep your existing HTML generation)
    analysis_html = f"""
<div style="font-family: system-ui, -apple-system, sans-serif;">
<div style="background: linear-gradient(135deg, #6366f1, #8b5cf6); border-radius: 12px; padding: 16px; text-align: center; margin-bottom: 12px;">
    <div style="font-size: 11px; opacity: 0.7;">MATCH SCORE</div>
    <div style="font-size: 42px; font-weight: 700; line-height: 1;">{score}%</div>
    <div style="font-size: 12px;">{'🎉 Excellent' if score >= 80 else '👍 Good' if score >= 60 else '⚠️ Needs Work'}</div>
</div>
<div style="text-align: center; font-size: 12px;">📊 {total_matched} out of {total_keywords} keywords matched</div>
<div style="text-align: center; font-size: 10px; color: #64748b; margin-top: 12px;">🔍 RAG Analysis</div>
</div>
"""
    
    return {
        "match_score": score,
        "missing_keywords": all_missing[:20],
        "analysis": analysis_html,
        "resume_length": len(resume_text.split()),
        "category_results": category_results,
        "total_keywords": total_keywords,
        "matched_keywords": total_matched
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 AI Resume Analyzer is running!")
    print("📱 Open: http://127.0.0.1:8000")
    print("💾 User data is now PERSISTENT (saved to users_db.json)")
    print("="*60 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)