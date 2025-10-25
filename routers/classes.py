from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import secrets
import string

from database.connection import get_db
from services.AuthService import get_current_user, get_current_teacher, get_current_student
from models.User import User
from models.Quiz import Class
from pydantic import BaseModel

router = APIRouter()

# Pydantic models
class ClassCreate(BaseModel):
    name: str
    description: str = None
    max_students: int = 50

class ClassJoin(BaseModel):
    class_code: str

class ClassResponse(BaseModel):
    id: int
    name: str
    description: str = None
    class_code: str
    teacher_name: str
    student_count: int
    max_students: int
    created_at: str

def generate_class_code() -> str:
    """Generate a unique 6-character class code"""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

@router.post("/", response_model=ClassResponse)
async def create_class(
    class_data: ClassCreate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Create a new class (teacher only)"""
    
    # Generate unique class code
    while True:
        class_code = generate_class_code()
        existing = db.query(Class).filter(Class.class_code == class_code).first()
        if not existing:
            break
    
    # Create new class
    new_class = Class(
        name=class_data.name,
        description=class_data.description,
        teacher_id=current_user.id,
        class_code=class_code,
        max_students=class_data.max_students
    )
    
    db.add(new_class)
    db.commit()
    db.refresh(new_class)
    
    return ClassResponse(
        id=new_class.id,
        name=new_class.name,
        description=new_class.description,
        class_code=new_class.class_code,
        teacher_name=current_user.name,
        student_count=0,
        max_students=new_class.max_students,
        created_at=new_class.created_at.isoformat()
    )

@router.get("/", response_model=List[ClassResponse])
async def get_classes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get classes for current user (teacher's created classes or student's enrolled class)"""
    
    if current_user.is_teacher:
        # Get teacher's classes
        classes = db.query(Class).filter(Class.teacher_id == current_user.id).all()
        
        result = []
        for class_obj in classes:
            student_count = db.query(User).filter(User.class_id == class_obj.id).count()
            
            result.append(ClassResponse(
                id=class_obj.id,
                name=class_obj.name,
                description=class_obj.description,
                class_code=class_obj.class_code,
                teacher_name=current_user.name,
                student_count=student_count,
                max_students=class_obj.max_students,
                created_at=class_obj.created_at.isoformat()
            ))
        
        return result
    
    else:
        # Get student's enrolled class
        if not current_user.class_id:
            return []
        
        class_obj = db.query(Class).filter(Class.id == current_user.class_id).first()
        if not class_obj:
            return []
        
        teacher = db.query(User).filter(User.id == class_obj.teacher_id).first()
        student_count = db.query(User).filter(User.class_id == class_obj.id).count()
        
        return [ClassResponse(
            id=class_obj.id,
            name=class_obj.name,
            description=class_obj.description,
            class_code=class_obj.class_code,
            teacher_name=teacher.name if teacher else "Unknown",
            student_count=student_count,
            max_students=class_obj.max_students,
            created_at=class_obj.created_at.isoformat()
        )]

@router.post("/join")
async def join_class(
    join_data: ClassJoin,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Join a class using class code (student only)"""
    
    # Find class by code
    class_obj = db.query(Class).filter(
        Class.class_code == join_data.class_code.upper(),
        Class.is_active == True
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found with this code"
        )
    
    # Check if class is full
    current_students = db.query(User).filter(User.class_id == class_obj.id).count()
    if current_students >= class_obj.max_students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class is full"
        )
    
    # Check if student is already in a class
    if current_user.class_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already enrolled in a class"
        )
    
    # Join the class
    current_user.class_id = class_obj.id
    db.commit()
    
    return {
        "message": f"Successfully joined class '{class_obj.name}'",
        "class_id": class_obj.id,
        "class_name": class_obj.name
    }

@router.get("/{class_id}/students", response_model=List[dict])
async def get_class_students(
    class_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get students in a specific class (teacher only)"""
    
    # Verify teacher owns this class
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.teacher_id == current_user.id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or access denied"
        )
    
    # Get students
    students = db.query(User).filter(User.class_id == class_id).all()
    
    return [student.to_dict() for student in students]

@router.delete("/{class_id}")
async def delete_class(
    class_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Delete a class (teacher only)"""
    
    # Verify teacher owns this class
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.teacher_id == current_user.id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or access denied"
        )
    
    # Remove students from class
    students = db.query(User).filter(User.class_id == class_id).all()
    for student in students:
        student.class_id = None
    
    # Delete the class
    db.delete(class_obj)
    db.commit()
    
    return {"message": "Class deleted successfully"}

@router.post("/leave")
async def leave_class(
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Leave current class (student only)"""
    
    if not current_user.class_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not enrolled in any class"
        )
    
    current_user.class_id = None
    db.commit()
    
    return {"message": "Successfully left the class"}
