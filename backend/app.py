from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS - Allow all
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/api/health")
def health():
    return {"status": "healthy"}

@app.post("/api/auth/register")
def register():
    return {"success": True, "message": "Registration successful"}

@app.post("/api/auth/login")
def login():
    return {"success": True, "message": "Login successful"}

@app.get("/api/auth/verify")
def verify():
    return {"valid": True}

@app.post("/api/upload")
def upload():
    return {"message": "Upload successful"}

@app.post("/api/analyze")
def analyze():
    return {"match_score": 75, "missing_keywords": ["python", "react"], "analysis": "Test analysis"}