import sqlite3
import os
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from datetime import datetime

DATABASE_PATH = "students.db"

def init_database():
    """Initialize database with tables"""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no VARCHAR(20) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                name VARCHAR(100) NOT NULL,
                department VARCHAR(100) NOT NULL,
                branch VARCHAR(100) NOT NULL,
                semester VARCHAR(10) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

@contextmanager
def get_db_connection():
    """Database connection context manager"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

class StudentDB:
    @staticmethod
    def create_student(roll_no: str, name: str, department: str, branch: str, semester: str) -> bool:
        """Create a new student"""
        try:
            with get_db_connection() as conn:
                # Hash the password (roll_no) before storing
                from server.auth import hash_password
                hashed_password = hash_password(roll_no)
                conn.execute("""
                    INSERT INTO students (roll_no, password, name, department, branch, semester)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (roll_no, hashed_password, name, department, branch, semester))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False  # Roll number already exists
    
    @staticmethod
    def get_student_by_roll_no(roll_no: str) -> Optional[Dict[str, Any]]:
        """Get student by roll number"""
        with get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM students WHERE roll_no = ?
            """, (roll_no,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_all_students() -> List[Dict[str, Any]]:
        """Get all students"""
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM students ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def delete_student(student_id: int) -> bool:
        """Delete a student"""
        try:
            with get_db_connection() as conn:
                conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
                conn.commit()
                return True
        except:
            return False
    
    @staticmethod
    def update_student_password(roll_no: str, new_password: str) -> bool:
        """Update student password"""
        try:
            with get_db_connection() as conn:
                conn.execute("""
                    UPDATE students SET password = ? WHERE roll_no = ?
                """, (new_password, roll_no))
                conn.commit()
                return True
        except:
            return False