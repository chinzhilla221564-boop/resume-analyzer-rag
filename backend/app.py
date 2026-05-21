from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import hashlib
import jwt
import os
import json
from pathlib import Path

app = FastAPI()

# ============================================
# CORS - Allow all origins
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# DATABASE (Persistent JSON)
# ============================================
DB_PATH = Path("/tmp/users_db.json")

def load_users():
    if DB_PATH.exists():
        try:
            with open(DB_PATH, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    with open(DB_PATH, 'w') as f:
        json.dump(users, f)

# ============================================
# JWT HELPER FUNCTIONS
# ============================================
SECRET_KEY = "resume-ai-secret-key-2025"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(email: str) -> str:
    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("email")
    except:
        return None

# ============================================
# HEALTH CHECK
# ============================================
@app.get("/")
@app.get("/api/health")
def health_check():
    return {"status": "healthy", "message": "API is running"}

# ============================================
# REGISTER
# ============================================
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

@app.post("/api/auth/register")
def register_user(data: RegisterRequest):
    users = load_users()
    
    if data.email in users:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    users[data.email] = {
        "name": data.name,
        "email": data.email,
        "password": hash_password(data.password),
        "created_at": datetime.now().isoformat()
    }
    
    save_users(users)
    token = create_token(data.email)
    
    return {
        "success": True,
        "message": "Registration successful!",
        "token": token,
        "user": {
            "name": data.name,
            "email": data.email
        }
    }

# ============================================
# LOGIN
# ============================================
class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/auth/login")
def login_user(data: LoginRequest):
    users = load_users()
    
    if data.email not in users:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    if users[data.email]["password"] != hash_password(data.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    token = create_token(data.email)
    
    return {
        "success": True,
        "message": "Login successful!",
        "token": token,
        "user": {
            "name": users[data.email]["name"],
            "email": data.email
        }
    }

# ============================================
# LOGOUT
# ============================================
@app.post("/api/auth/logout")
def logout_user():
    return {"success": True, "message": "Logged out successfully"}

# ============================================
# VERIFY TOKEN
# ============================================
@app.get("/api/auth/verify")
def verify_user_token(token: str):
    email = verify_token(token)
    users = load_users()
    
    if not email or email not in users:
        raise HTTPException(status_code=401, detail="Invalid token")
    
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
resume_storage = {}

# ============================================
# UPLOAD RESUME
# ============================================
@app.post("/api/upload")
def upload_resume(file: UploadFile = File(...), token: str = None):
    email = verify_token(token)
    
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    content = file.file.read()
    text_content = content.decode('utf-8', errors='ignore')[:5000]
    
    resume_storage[email] = {
        "text": text_content,
        "filename": file.filename,
        "uploaded_at": datetime.now().isoformat()
    }
    
    return {
        "success": True,
        "message": f"✅ {file.filename} uploaded successfully!",
        "text_length": len(text_content),
        "word_count": len(text_content.split())
    }

# ============================================
# ANALYZE RESUME
# ============================================
class AnalyzeRequest(BaseModel):
    job_description: str
    token: str

@app.post("/api/analyze")
def analyze_resume(data: AnalyzeRequest):
    email = verify_token(data.token)
    
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if email not in resume_storage:
        raise HTTPException(status_code=400, detail="No resume uploaded. Please upload a resume first.")
    
    resume_text = resume_storage[email]["text"].lower()
    job_lower = data.job_description.lower()
    
    # Keywords to check
    keywords = [
        'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
        'node.js', 'express', 'django', 'sql', 'mysql', 'postgresql', 'mongodb',
        'aws', 'azure', 'docker', 'kubernetes', 'git', 'github', 'leadership',
        'communication', 'teamwork', 'agile', 'scrum'
    ]
    
    missing = []
    matched = []
    
    for kw in keywords:
        if kw in job_lower:
            if kw in resume_text:
                matched.append(kw)
            else:
                missing.append(kw)
    
    total = len([kw for kw in keywords if kw in job_lower])
    matched_count = len(matched)
    score = int((matched_count / total) * 100) if total > 0 else 50
    
    # Generate analysis
    analysis_text = f"""
{'='*60}
📊 RESUME ANALYSIS REPORT
{'='*60}

🎯 MATCH SCORE: {score}%

✅ MATCHED KEYWORDS ({len(matched)}):
{chr(10).join(f'   • {kw}' for kw in matched[:15]) if matched else '   • None'}

❌ MISSING KEYWORDS ({len(missing)}):
{chr(10).join(f'   • {kw}' for kw in missing[:15]) if missing else '   • None - Great job!'}

💡 RECOMMENDATIONS:
   • Add the missing keywords to your skills section
   • Quantify your achievements with numbers
   • Use action verbs (Developed, Built, Led)
   • Tailor your resume for each job application

{'='*60}
🔍 Powered by RAG Technology
"""
    
    # Save to history
    users = load_users()
    if email in users:
        history_entry = {
            "date": datetime.now().isoformat(),
            "score": score,
            "job_title": data.job_description[:50],
            "missing_count": len(missing)
        }
        if "resume_history" not in users[email]:
            users[email]["resume_history"] = []
        users[email]["resume_history"].insert(0, history_entry)
        if len(users[email]["resume_history"]) > 10:
            users[email]["resume_history"] = users[email]["resume_history"][:10]
        save_users(users)
    
    return {
        "success": True,
        "match_score": score,
        "missing_keywords": missing,
        "analysis": analysis_text,
        "resume_length": len(resume_text.split()),
        "total_keywords": total,
        "matched_keywords": matched_count
    }

# ============================================
# RUN SERVER
# ============================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)