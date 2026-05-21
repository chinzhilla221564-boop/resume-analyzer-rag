from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import tempfile
import os
from pathlib import Path
import PyPDF2
import docx
import jwt
import json
from datetime import datetime, timedelta
from typing import Optional
import hashlib

app = FastAPI()

# ============================================
# DATABASE FUNCTIONS (No external file needed)
# ============================================
DB_PATH = Path(__file__).parent / "users_db.json"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if DB_PATH.exists():
        with open(DB_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(DB_PATH, 'w') as f:
        json.dump(users, f, indent=2)

def init_db():
    if not DB_PATH.exists():
        save_users({})
        print("✅ Database created")

# Initialize database
init_db()

# ============================================
# CORS CONFIGURATION
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://chinzhilla221564-boop.github.io",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Handle OPTIONS requests
@app.options("/{path:path}")
async def options_handler(path: str):
    return Response(status_code=200, headers={
        "Access-Control-Allow-Origin": "https://chinzhilla221564-boop.github.io",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    })

# ============================================
# HEALTH & ROOT ROUTES
# ============================================

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.get("/")
async def root():
    return {"message": "AI Resume Analyzer API", "status": "running"}

SECRET_KEY = "your-secret-key-resume-ai-2025"
ALGORITHM = "HS256"

# ============================================
# STATIC FILES MOUNTING
# ============================================
frontend_path = Path(__file__).parent.parent / "frontend"
css_path = frontend_path / "css"
js_path = frontend_path / "js"

if css_path.exists():
    app.mount("/css", StaticFiles(directory=str(css_path)), name="css")
if js_path.exists():
    app.mount("/js", StaticFiles(directory=str(js_path)), name="js")

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
    
    return {
        "success": True,
        "message": "Registration successful!",
        "token": token,
        "user": {
            "name": user.name,
            "email": user.email
        }
    }

@app.post("/api/auth/login")
async def login(user: UserLogin):
    users = load_users()
    
    if user.email not in users:
        raise HTTPException(400, "Invalid email or password")
    
    if not verify_password(user.password, users[user.email]["password"]):
        raise HTTPException(400, "Invalid email or password")
    
    token = create_token(user.email)
    
    return {
        "success": True,
        "message": "Login successful!",
        "token": token,
        "user": {
            "name": users[user.email]["name"],
            "email": user.email
        }
    }

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
# RESUME STORAGE
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
    
    # Quick analysis response
    analysis_html = f"""
<div style="text-align: center; padding: 20px;">
    <div style="font-size: 48px; font-weight: bold; color: #6366f1;">{score}%</div>
    <div style="margin: 10px 0;">Match Score</div>
    <div>Missing Keywords: {', '.join(all_missing[:8])}</div>
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
    port = int(os.environ.get("PORT", 8000))
    print(f"\n{'='*60}")
    print("🚀 AI Resume Analyzer is running!")
    print(f"📱 Open: http://localhost:{port}")
    print(f"{'='*60}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)