from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import json

from ..database import StudentDB
from ..auth import verify_password, generate_token, verify_token
from ..models import StudentLogin, StudentRegister, StudentResponse

router = APIRouter()
security = HTTPBearer()

def get_current_student(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current authenticated student"""
    token = credentials.credentials
    student_data = verify_token(token)
    if not student_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return student_data

@router.post("/login")
async def login(student_data: StudentLogin):
    """Student login endpoint"""
    # Get student from database
    student = StudentDB.get_student_by_roll_no(student_data.roll_no)
    if not student:
        raise HTTPException(status_code=401, detail="Invalid roll number or password")
    
    # Verify password
    if not verify_password(student_data.password, student['password']):
        raise HTTPException(status_code=401, detail="Invalid roll number or password")
    
    # Generate token
    token = generate_token(student)
    
    return {
        "token": token,
        "student": {
            "id": student['id'],
            "roll_no": student['roll_no'],
            "name": student['name'],
            "department": student['department'],
            "branch": student['branch'],
            "semester": student['semester']
        }
    }

@router.post("/logout")
async def logout(current_student: dict = Depends(get_current_student)):
    """Student logout endpoint"""
    # In a real implementation, you'd invalidate the token
    # For simplicity, we'll just return success
    return {"message": "Logged out successfully"}

@router.get("/me")
async def get_current_user(current_student: dict = Depends(get_current_student)):
    """Get current student information"""
    return current_student

@router.post("/students/register")
async def register_student(student_data: StudentRegister):
    """Admin endpoint to register new student"""
    # Create student
    success = StudentDB.create_student(
        student_data.roll_no,
        student_data.name,
        student_data.department,
        student_data.branch,
        student_data.semester
    )
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Roll number already exists")
    return {"message": "Student registered successfully"}

@router.get("/students")
async def get_all_students():
    """Admin endpoint to get all students"""
    students = StudentDB.get_all_students()
    return {"students": students} 