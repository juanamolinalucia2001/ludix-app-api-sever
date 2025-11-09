"""
Router de quizzes usando exclusivamente Supabase
Para docentes: crear quizzes, gestionar preguntas
Para estudiantes: ver quizzes disponibles
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Any

from services.supabase_service import supabase_service
from routers.auth_supabase import get_current_user

router = APIRouter()

# Pydantic models
class QuestionCreate(BaseModel):
    question_text: str
    question_type: str = "multiple_choice"
    options: List[str]
    correct_answer: int
    explanation: Optional[str] = None
    difficulty: str = "medium"
    points: int = 10
    time_limit: int = 30

class QuestionResponse(BaseModel):
    id: str
    question_text: str
    question_type: str
    options: List[str]
    correct_answer: int
    explanation: Optional[str]
    difficulty: str
    points: int
    time_limit: int
    order_index: int

class QuizCreate(BaseModel):
    title: str
    description: Optional[str] = None
    class_id: str
    time_limit: Optional[int] = None
    difficulty: str = "medium"
    topic: Optional[str] = None
    questions: List[QuestionCreate]

class QuizResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    creator_id: str
    class_id: str
    time_limit: Optional[int]
    difficulty: Optional[str] = "MEDIUM"
    is_active: bool
    is_published: bool
    topic: Optional[str]
    created_at: str
    questions: Optional[List[QuestionResponse]] = None

class QuizListItem(BaseModel):
    id: str
    title: str
    description: Optional[str]
    difficulty: Optional[str] = "MEDIUM"
    is_active: bool
    is_published: bool
    questions_count: int
    total_points: int
    created_at: str

@router.post("/", response_model=QuizResponse)
async def create_quiz(
    quiz_data: QuizCreate,
    current_user: dict = Depends(get_current_user)
):
    """Crear nuevo quiz con preguntas (solo docentes)"""
    try:
        if current_user["role"].upper() != "TEACHER":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can create quizzes"
            )
        
        # Crear el quiz
        new_quiz = await supabase_service.create_quiz(
            title=quiz_data.title,
            description=quiz_data.description or "",
            questions=[],  # Se agregarán después
            class_id=quiz_data.class_id,
            created_by=current_user["id"]
        )
        
        # Crear las preguntas
        questions = []
        for i, question_data in enumerate(quiz_data.questions):
            question = await supabase_service.create_question({
                "quiz_id": new_quiz["id"],
                "question_text": question_data.question_text,
                "question_type": question_data.question_type,
                "options": question_data.options,
                "correct_answer": question_data.correct_answer,
                "explanation": question_data.explanation,
                "difficulty": question_data.difficulty,
                "points": question_data.points,
                "time_limit": question_data.time_limit,
                "order_index": i
            })
            questions.append(QuestionResponse(**question))
        
        # Retornar quiz con preguntas
        quiz_response = QuizResponse(**new_quiz)
        quiz_response.questions = questions
        
        return quiz_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating quiz: {str(e)}"
        )

@router.get("/class/{class_id}", response_model=List[QuizListItem])
async def get_class_quizzes(
    class_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtener quizzes de una clase"""
    try:
        # Verificar acceso
        if current_user["role"].upper() == "TEACHER":
            # Los docentes pueden ver todos sus quizzes
            quizzes = await supabase_service.get_class_quizzes(class_id)
        elif current_user["role"].upper() == "STUDENT":
            # Los estudiantes solo ven quizzes publicados
            if current_user.get("class_id") != class_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Students can only access their own class quizzes"
                )
            quizzes = await supabase_service.get_class_quizzes(class_id)
            # Filtrar solo publicados para estudiantes
            quizzes = [q for q in quizzes if q.get("is_published", False)]
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Formatear respuesta
        quiz_items = []
        for quiz in quizzes:
            # Obtener preguntas para contar
            questions = await supabase_service.get_quiz_questions(quiz["id"])
            total_points = sum(q.get("points", 10) for q in questions)
            
            quiz_items.append(QuizListItem(
                id=quiz["id"],
                title=quiz["title"],
                description=quiz.get("description"),
                difficulty=quiz.get("difficulty", "medium"),
                is_active=quiz.get("is_active", True),
                is_published=quiz.get("is_published", False),
                questions_count=len(questions),
                total_points=total_points,
                created_at=quiz.get("created_at", "")
            ))
        
        return quiz_items
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting class quizzes: {str(e)}"
        )

@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtener quiz completo con preguntas"""
    try:
        quiz = await supabase_service.get_quiz_by_id(quiz_id)
        
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found"
            )
        
        # Verificar acceso
        if current_user["role"].upper() == "STUDENT":
            if not quiz.get("is_published", False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Quiz is not published"
                )
            if current_user.get("class_id") != quiz["class_id"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Students can only access their own class quizzes"
                )
        
        # Obtener preguntas
        questions = await supabase_service.get_quiz_questions(quiz_id)
        
        # Si es estudiante, no mostrar respuestas correctas
        if current_user["role"].upper() == "STUDENT":
            for question in questions:
                question.pop("correct_answer", None)
                question.pop("explanation", None)
        
        quiz_response = QuizResponse(**quiz)
        quiz_response.questions = [QuestionResponse(**q) for q in questions]
        
        return quiz_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting quiz: {str(e)}"
        )

@router.put("/{quiz_id}/publish")
async def publish_quiz(
    quiz_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Publicar quiz (solo docentes)"""
    try:
        if current_user["role"].upper() != "TEACHER":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can publish quizzes"
            )
        
        # Actualizar quiz
        result = supabase_service.client.table("quizzes").update({
            "is_published": True,
            "published_at": supabase_service.client.functions.invoke("now"),
            "updated_at": supabase_service.client.functions.invoke("now")
        }).eq("id", quiz_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found"
            )
        
        return {"message": "Quiz published successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error publishing quiz: {str(e)}"
        )

@router.delete("/{quiz_id}")
async def delete_quiz(
    quiz_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Eliminar quiz (solo docentes)"""
    try:
        if current_user["role"].upper() != "TEACHER":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can delete quizzes"
            )
        
        # Marcar como inactivo en lugar de eliminar
        result = supabase_service.client.table("quizzes").update({
            "is_active": False,
            "updated_at": supabase_service.client.functions.invoke("now")
        }).eq("id", quiz_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found"
            )
        
        return {"message": "Quiz deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting quiz: {str(e)}"
        )
