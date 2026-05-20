"""
Run both backend and frontend servers
"""
import subprocess
import threading
import time
import webbrowser

def run_backend():
    subprocess.run(["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])

def run_frontend():
    time.sleep(2)  # Wait for backend to start
    webbrowser.open("http://localhost:8000")  # FastAPI serves static files
    # Or use Python's HTTP server for static files
    subprocess.run(["python", "-m", "http.server", "3000", "--directory", "frontend"])

if __name__ == "__main__":
    print("🚀 Starting AI Resume Analyzer...")
    print("📡 Backend: http://localhost:8000")
    print("🎨 Frontend: http://localhost:3000")
    
    # Start backend in thread
    backend_thread = threading.Thread(target=run_backend)
    backend_thread.start()
    
    # Wait a bit
    time.sleep(3)
    
    # Start frontend
    frontend_thread = threading.Thread(target=run_frontend)
    frontend_thread.start()