from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.connection import get_db
from services.AuthService import get_current_user, get_current_teacher, get_current_student
from models.User import User
from pydantic import BaseModel

router = APIRouter()

# Pydantic models
class UserProfile(BaseModel):
    name: str
    avatar_url: str = None
    mascot: str = None

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    is_active: bool
    avatar_url: str = None
    class_id: int = None
    mascot: str = None
    created_at: str

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile information"""
    return UserResponse(**current_user.to_dict())

@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_data: UserProfile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    
    # Update user fields
    current_user.name = profile_data.name
    if profile_data.avatar_url:
        current_user.avatar_url = profile_data.avatar_url
    if profile_data.mascot and current_user.is_student:
        current_user.mascot = profile_data.mascot
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse(**current_user.to_dict())

@router.get("/students", response_model=List[UserResponse])
async def get_class_students(
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get all students in teacher's classes"""
    
    # Get students from teacher's classes
    students = db.query(User).join(
        User.class_enrolled
    ).filter(
        User.role == 'student',
        User.class_enrolled.has(teacher_id=current_user.id)
    ).all()
    
    return [UserResponse(**student.to_dict()) for student in students]

@router.get("/teacher/dashboard")
async def get_teacher_dashboard(
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get teacher dashboard data"""
    
    # Get teacher's classes and students
    from models.Quiz import Class
    from models.GameSession import GameSession
    
    classes = db.query(Class).filter(Class.teacher_id == current_user.id).all()
    
    dashboard_data = {
        "teacher": current_user.to_dict(),
        "classes": [],
        "total_students": 0,
        "total_games": 0,
        "recent_activity": []
    }
    
    for class_obj in classes:
        students = db.query(User).filter(User.class_id == class_obj.id).all()
        
        class_data = {
            "id": class_obj.id,
            "name": class_obj.name,
            "description": class_obj.description,
            "class_code": class_obj.class_code,
            "student_count": len(students),
            "students": [student.to_dict() for student in students]
        }
        
        dashboard_data["classes"].append(class_data)
        dashboard_data["total_students"] += len(students)
    
    return dashboard_data
