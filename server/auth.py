import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
TOKEN_EXPIRY_HOURS = 24

def hash_password(password: str) -> str:
    """Simple password storage - just return the password"""
    return password

def verify_password(password: str, hashed: str) -> bool:
    """Simple password verification - direct comparison"""
    return password == hashed

def generate_token(student_data: Dict[str, Any]) -> str:
    """Generate JWT token for student"""
    payload = {
        'student_id': student_data['id'],
        'roll_no': student_data['roll_no'],
        'name': student_data['name'],
        'department': student_data['department'],
        'branch': student_data['branch'],
        'semester': student_data['semester'],
        'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def generate_session_token() -> str:
    """Generate random session token"""
    return secrets.token_urlsafe(32) 