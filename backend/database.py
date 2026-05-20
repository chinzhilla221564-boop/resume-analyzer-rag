import json
import os
from pathlib import Path
from datetime import datetime
import hashlib

# Database file path
DB_PATH = Path(__file__).parent / "users_db.json"

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load users from JSON file"""
    if DB_PATH.exists():
        try:
            with open(DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    """Save users to JSON file"""
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, default=str)

def init_db():
    """Initialize database file"""
    if not DB_PATH.exists():
        save_users({})
        print(f"✅ Database created at: {DB_PATH}")
    else:
        print(f"✅ Database loaded from: {DB_PATH}")