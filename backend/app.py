from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
from datetime import datetime, timedelta
import jwt
import hashlib

app = FastAPI()

# Simple in-memory database (for testing)
users_db = {}

# ============================================
# CORS - Simplified
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Simple routes for testing
# ============================================

@app.get("/")
def root():
    return {"message": "API is running"}

@app.get("/api/health")
def health():
    return {"status": "healthy"}

# ============================================
# Simple Registration
# ============================================

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

@app.post("/api/auth/register")
async def register(data: RegisterRequest):
    # Simple registration - no database for now
    return {
        "success": True,
        "message": "Registration successful!",
        "token": "test-token-123",
        "user": {
            "name": data.name,
            "email": data.email
        }
    }

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/auth/login")
async def login(data: LoginRequest):
    return {
        "success": True,
        "message": "Login successful!",
        "token": "test-token-123",
        "user": {
            "name": "Test User",
            "email": data.email
        }
    }

@app.get("/api/auth/verify")
async def verify(token: str):
    return {"valid": True, "user": {"name": "Test User", "email": "test@test.com"}}

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    return {"message": f"File uploaded successfully", "filename": file.filename}

@app.post("/api/analyze")
async def analyze(data: dict):
    return {
        "match_score": 75,
        "missing_keywords": ["python", "react", "aws"],
        "analysis": "Your resume matches well with the job description...",
        "resume_length": 500
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)