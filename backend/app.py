from fastapi import FastAPI, UploadFile, File, HTTPException
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
from datetime import datetime, timedelta
from typing import Optional
from backend.database import load_users, save_users, hash_password, init_db

app = FastAPI()

# Initialize database
init_db()

# Secret key for JWT
SECRET_KEY = "your-secret-key-resume-ai-2025"
ALGORITHM = "HS256"

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# STATIC FILES MOUNTING
# ============================================
frontend_path = Path(__file__).parent.parent / "frontend"
css_path = frontend_path / "css"
js_path = frontend_path / "js"

css_path.mkdir(parents=True, exist_ok=True)
js_path.mkdir(parents=True, exist_ok=True)

# Mount static directories
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
    """Verify password"""
    return hash_password(password) == hashed

def create_token(email: str) -> str:
    """Create JWT token"""
    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[str]:
    """Verify JWT token"""
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
    """Register new user"""
    users = load_users()
    
    # Check if user already exists
    if user.email in users:
        raise HTTPException(400, "Email already registered")
    
    # Create new user
    users[user.email] = {
        "name": user.name,
        "email": user.email,
        "password": hash_password(user.password),
        "created_at": datetime.now().isoformat(),
        "resume_history": []
    }
    
    # Save to database
    save_users(users)
    
    # Create token
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
    """Login user"""
    users = load_users()
    
    # Check if user exists
    if user.email not in users:
        raise HTTPException(400, "Invalid email or password")
    
    # Verify password
    if not verify_password(user.password, users[user.email]["password"]):
        raise HTTPException(400, "Invalid email or password")
    
    # Create token
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
    """Logout user"""
    return {"success": True, "message": "Logged out successfully"}

@app.get("/api/auth/verify")
async def verify(token: str):
    """Verify token"""
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
    """Extract text from different file types"""
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

@app.get("/")
async def root():
    index_path = Path(__file__).parent.parent / "frontend" / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse("<h1>Frontend not found</h1>")

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
    
    # Save to user history in persistent database
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
    
    # Compact HTML analysis
    analysis_html = f"""
<div style="font-family: system-ui, -apple-system, sans-serif;">

<!-- Score -->
<div style="background: linear-gradient(135deg, #6366f1, #8b5cf6); border-radius: 12px; padding: 16px; text-align: center; margin-bottom: 12px;">
    <div style="font-size: 11px; opacity: 0.7;">MATCH SCORE</div>
    <div style="font-size: 42px; font-weight: 700; line-height: 1;">{score}%</div>
    <div style="font-size: 12px;">{'🎉 Excellent' if score >= 80 else '👍 Good' if score >= 60 else '⚠️ Needs Work'}</div>
    <div style="background: rgba(255,255,255,0.2); border-radius: 6px; height: 4px; margin-top: 10px;">
        <div style="background: white; width: {score}%; height: 4px; border-radius: 6px;"></div>
    </div>
</div>

<!-- Resume Info -->
<div style="background: rgba(255,255,255,0.04); border-radius: 10px; padding: 10px 12px; margin-bottom: 12px; font-size: 12px;">
    <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
        <span>📄 Resume</span>
        <span>📊 {len(resume_text.split())} words</span>
    </div>
</div>

<!-- Skills -->
<div style="background: rgba(255,255,255,0.04); border-radius: 10px; padding: 12px; margin-bottom: 12px;">
    <div style="font-size: 13px; font-weight: 600; margin-bottom: 10px;">📈 Skills</div>
"""
    
    for category, results in category_results.items():
        match_percent = int((results["match_count"] / results["total_relevant"]) * 100) if results["total_relevant"] > 0 else 0
        analysis_html += f"""
    <div style="margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; font-size: 12px;">
            <span>{category}</span>
            <span style="color: {'#10b981' if match_percent >= 70 else '#f59e0b'};">{match_percent}%</span>
        </div>
        <div style="background: #1e293b; border-radius: 4px; height: 3px;">
            <div style="background: {'#10b981' if match_percent >= 70 else '#f59e0b'}; width: {match_percent}%; height: 3px; border-radius: 4px;"></div>
        </div>
"""
        if results["missing"]:
            missing_short = ', '.join(results["missing"][:3])
            if len(results["missing"]) > 3:
                missing_short += f' +{len(results["missing"])-3}'
            analysis_html += f'        <div style="font-size: 10px; color: #f87171; margin-top: 3px;">✗ {missing_short}</div>\n'
        analysis_html += "    </div>\n"
    
    analysis_html += """
</div>

<!-- Missing Keywords -->
<div style="background: rgba(255,255,255,0.04); border-radius: 10px; padding: 12px; margin-bottom: 12px;">
    <div style="font-size: 13px; font-weight: 600; margin-bottom: 8px;">📋 Missing</div>
    <div style="display: flex; flex-wrap: wrap; gap: 5px;">
"""
    
    for kw in all_missing[:12]:
        analysis_html += f'        <span style="background: rgba(239,68,68,0.15); color: #f87171; padding: 2px 8px; border-radius: 14px; font-size: 10px;">+{kw}</span>\n'
    
    analysis_html += """
    </div>
</div>

<!-- Tips -->
<div style="background: rgba(255,255,255,0.04); border-radius: 10px; padding: 12px; margin-bottom: 12px;">
    <div style="font-size: 13px; font-weight: 600; margin-bottom: 6px;">💡 Tips</div>
    <div style="font-size: 11px; line-height: 1.4;">
        • Add missing keywords<br>
        • Use numbers (e.g., "Improved 30%")<br>
        • Use action verbs (Developed, Led)
    </div>
</div>

<!-- Stats -->
<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 8px;">
    <div style="background: rgba(255,255,255,0.04); border-radius: 8px; padding: 8px; text-align: center;">
        <div style="font-size: 18px; font-weight: 700;">{total_keywords}</div>
        <div style="font-size: 9px;">Analyzed</div>
    </div>
    <div style="background: rgba(255,255,255,0.04); border-radius: 8px; padding: 8px; text-align: center;">
        <div style="font-size: 18px; font-weight: 700; color: #10b981;">{total_matched}</div>
        <div style="font-size: 9px;">Matched</div>
    </div>
    <div style="background: rgba(255,255,255,0.04); border-radius: 8px; padding: 8px; text-align: center;">
        <div style="font-size: 18px; font-weight: 700; color: #ef4444;">{len(all_missing)}</div>
        <div style="font-size: 9px;">Missing</div>
    </div>
    <div style="background: rgba(255,255,255,0.04); border-radius: 8px; padding: 8px; text-align: center;">
        <div style="font-size: 18px; font-weight: 700;">{len(category_results)}</div>
        <div style="font-size: 9px;">Categories</div>
    </div>
</div>

<div style="text-align: center; font-size: 9px; color: #64748b;">🔍 RAG Analysis</div>
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