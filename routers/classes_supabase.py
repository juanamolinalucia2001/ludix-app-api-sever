"""
Router de clases usando exclusivamente Supabase
Para docentes: crear aulas, ver estudiantes, estadísticas
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional

from services.supabase_service import supabase_service
from routers.auth_supabase import get_current_user

router = APIRouter()

# Pydantic models
class ClassCreate(BaseModel):
    name: str
    description: Optional[str] = None
    max_students: Optional[int] = 30

class ClassResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    teacher_id: str
    class_code: str
    is_active: bool
    max_students: Optional[int]
    created_at: str

class StudentInClass(BaseModel):
    id: str
    name: str
    email: str
    avatar_url: Optional[str]
    mascot: Optional[str]
    last_login: Optional[str]

class ClassStatistics(BaseModel):
    students_count: int
    quizzes_count: int
    total_games_played: int
    average_score: float
    active_students: int

class StudentResult(BaseModel):
    student: StudentInClass
    total_games: int
    average_score: float
    best_score: int
    last_activity: Optional[str]

class JoinClassRequest(BaseModel):
    class_code: str

@router.post("/", response_model=ClassResponse)
async def create_class(
    class_data: ClassCreate,
    current_user: dict = Depends(get_current_user)
):
    """Crear nueva clase (solo docentes)"""
    try:
        if current_user["role"] != "teacher":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can create classes"
            )
        
        new_class = await supabase_service.create_class(
            name=class_data.name,
            description=class_data.description or "",
            teacher_id=current_user["id"]
        )
        
        return ClassResponse(**new_class)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating class: {str(e)}"
        )

@router.get("/my-classes", response_model=List[ClassResponse])
async def get_my_classes(current_user: dict = Depends(get_current_user)):
    """Obtener clases del docente actual"""
    try:
        if current_user["role"] != "teacher":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can access their classes"
            )
        
        classes = await supabase_service.get_teacher_classes(current_user["id"])
        return [ClassResponse(**class_data) for class_data in classes]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting classes: {str(e)}"
        )

@router.get("/{class_id}/students", response_model=List[StudentInClass])
async def get_class_students(
    class_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtener estudiantes de una clase"""
    try:
        if current_user["role"] != "teacher":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can view class students"
            )
        
        students = await supabase_service.get_class_students(class_id)
        
        return [
            StudentInClass(
                id=student["id"],
                name=student.get("name", ""),
                email=student["email"],
                avatar_url=student.get("avatar_url"),
                mascot=student.get("mascot"),
                last_login=student.get("last_login")
            )
            for student in students
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting class students: {str(e)}"
        )

@router.get("/{class_id}/statistics", response_model=ClassStatistics)
async def get_class_statistics(
    class_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtener estadísticas de una clase"""
    try:
        if current_user["role"] != "teacher":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can view class statistics"
            )
        
        stats = await supabase_service.get_class_statistics(class_id)
        return ClassStatistics(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting class statistics: {str(e)}"
        )

@router.get("/{class_id}/results", response_model=List[StudentResult])
async def get_class_results(
    class_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtener resultados de todos los estudiantes en la clase"""
    try:
        if current_user["role"] != "teacher":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can view class results"
            )
        
        results = await supabase_service.get_student_results_in_class(class_id)
        
        formatted_results = []
        for result in results:
            student_data = result["student"]
            formatted_results.append(
                StudentResult(
                    student=StudentInClass(
                        id=student_data["id"],
                        name=student_data.get("name", ""),
                        email=student_data["email"],
                        avatar_url=student_data.get("avatar_url"),
                        mascot=student_data.get("mascot"),
                        last_login=student_data.get("last_login")
                    ),
                    total_games=result["total_games"],
                    average_score=result["average_score"],
                    best_score=result["best_score"],
                    last_activity=result["last_activity"]
                )
            )
        
        return formatted_results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting class results: {str(e)}"
        )

# ================================
# ENDPOINTS PARA ESTUDIANTES
# ================================

@router.post("/join", response_model=dict)
async def join_class(
    join_data: JoinClassRequest,
    current_user: dict = Depends(get_current_user)
):
    """Unirse a una clase por código (solo estudiantes)"""
    try:
        if current_user["role"] != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can join classes"
            )
        
        result = await supabase_service.join_class_by_code(
            student_id=current_user["id"],
            class_code=join_data.class_code
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error joining class: {str(e)}"
        )

@router.get("/my-class", response_model=Optional[ClassResponse])
async def get_my_class(current_user: dict = Depends(get_current_user)):
    """Obtener la clase del estudiante actual"""
    try:
        if current_user["role"] != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can access their class"
            )
        
        if not current_user.get("class_id"):
            return None
        
        # Obtener información de la clase
        class_result = supabase_service.client.table("classes").select("*").eq("id", current_user["class_id"]).single().execute()
        
        if class_result.data:
            return ClassResponse(**class_result.data)
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting student class: {str(e)}"
        )
