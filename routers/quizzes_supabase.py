"""
Router de quizzes usando exclusivamente Supabase
Para docentes: crear quizzes, gestionar preguntas
Para estudiantes: ver quizzes disponibles
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone

from services.supabase_service import supabase_service
from routers.auth_supabase import get_current_user

router = APIRouter()

# ============================================================
# 🧩 MODELOS
# ============================================================

class QuestionCreate(BaseModel):
    question_text: str
    question_type: str = "multiple_choice"   # Python-side
    options: List[str]
    correct_answer: int
    explanation: Optional[str] = None
    difficulty: str = "medium"               # Python-side
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
    difficulty: str = "medium"               # Python-side
    topic: Optional[str] = None
    questions: List[QuestionCreate]

class QuizResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    creator_id: str
    class_id: str
    time_limit: Optional[int]
    difficulty: Optional[str] = "MEDIUM"     # DB-side
    is_active: bool
    is_published: bool
    topic: Optional[str]
    created_at: str
    questions: Optional[List[QuestionResponse]] = None

class QuizListItem(BaseModel):
    id: str
    title: str
    description: Optional[str]
    difficulty: Optional[str] = "MEDIUM"     # DB-side
    is_active: bool
    is_published: bool
    questions_count: int
    total_points: int
    created_at: str


# ============================================================
# 🚀 ENDPOINTS
# ============================================================

@router.post("/", response_model=QuizResponse)
async def create_quiz(
    quiz_data: QuizCreate,
    current_user: dict = Depends(get_current_user)
):
    """Crear nuevo quiz con preguntas (solo docentes)"""
    try:
        if current_user["role"].upper() != "TEACHER":
            raise HTTPException(status_code=403, detail="Only teachers can create quizzes")

        # Normalizar dificultad del quiz (si tu columna es enum en DB)
        quiz_difficulty_db = (quiz_data.difficulty or "MEDIUM").upper()

        # Crear el quiz
        new_quiz = await supabase_service.create_quiz(
            title=quiz_data.title,
            description=quiz_data.description or "",
            questions=[],  # se agregan luego
            class_id=quiz_data.class_id,
            created_by=current_user["id"],
            # si tu create_quiz soporta difficulty, pásalo:
            difficulty=quiz_difficulty_db
        )

        # Crear las preguntas
        questions = []
        for i, qd in enumerate(quiz_data.questions):
            # 🔁 ENUMS a MAYÚSCULAS para DB (Postgres enums)
            qt_db = (qd.question_type or "multiple_choice").upper()
            diff_db = (qd.difficulty or "MEDIUM").upper()

            question = await supabase_service.create_question({
                "quiz_id": new_quiz["id"],
                "question_text": qd.question_text,
                "question_type": qt_db,                  # 👈 enum DB
                "options": qd.options,
                "correct_answer": qd.correct_answer,
                "explanation": qd.explanation,
                "difficulty": diff_db,                   # 👈 enum DB
                "points": qd.points,
                "time_limit": qd.time_limit,
                "order_index": i
            })
            questions.append(QuestionResponse(**question))

        quiz_response = QuizResponse(**new_quiz)
        quiz_response.questions = questions
        return quiz_response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating quiz: {e}")


@router.get("/class/{class_id}", response_model=List[QuizListItem])
async def get_class_quizzes(
    class_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtener quizzes de una clase"""
    try:
        if current_user["role"].upper() == "TEACHER":
            quizzes = await supabase_service.get_class_quizzes(class_id)
        elif current_user["role"].upper() == "STUDENT":
            if current_user.get("class_id") != class_id:
                raise HTTPException(403, "Students can only access their own class quizzes")
            quizzes = await supabase_service.get_class_quizzes(class_id)
            quizzes = [q for q in quizzes if q.get("is_published", False)]
        else:
            raise HTTPException(403, "Access denied")

        quiz_items = []
        for quiz in quizzes:
            questions = await supabase_service.get_quiz_questions(quiz["id"])
            total_points = sum(q.get("points", 10) for q in questions)

            quiz_items.append(QuizListItem(
                id=quiz["id"],
                title=quiz["title"],
                description=quiz.get("description"),
                difficulty=quiz.get("difficulty", "MEDIUM"),
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
        raise HTTPException(status_code=500, detail=f"Error getting class quizzes: {e}")


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtener quiz completo con preguntas"""
    try:
        quiz = await supabase_service.get_quiz_by_id(quiz_id)
        if not quiz:
            raise HTTPException(404, "Quiz not found")

        if current_user["role"].upper() == "STUDENT":
            if not quiz.get("is_published", False):
                raise HTTPException(403, "Quiz is not published")
            if current_user.get("class_id") != quiz["class_id"]:
                raise HTTPException(403, "Students can only access their own class quizzes")

        questions = await supabase_service.get_quiz_questions(quiz_id)
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
        raise HTTPException(status_code=500, detail=f"Error getting quiz: {e}")


# ============================================================
# ✅ PUBLICAR / BORRAR
# ============================================================

@router.put("/{quiz_id}/publish")
async def publish_quiz(
    quiz_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Publicar quiz (solo docentes)"""
    if current_user["role"].upper() != "TEACHER":
        raise HTTPException(403, "Only teachers can publish quizzes")

    ts = datetime.now(timezone.utc).isoformat()

    try:
        result = supabase_service.client.table("quizzes").update({
            "is_published": True,
            "published_at": ts,
            "updated_at": ts,
        }).eq("id", quiz_id).execute()

        if not result.data:
            raise HTTPException(404, "Quiz not found")

        return {"message": "Quiz published successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot publish quiz: {e}")


@router.delete("/{quiz_id}")
async def delete_quiz(
    quiz_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Eliminar quiz (solo docentes)"""
    if current_user["role"].upper() != "TEACHER":
        raise HTTPException(403, "Only teachers can delete quizzes")

    ts = datetime.now(timezone.utc).isoformat()
    try:
        result = supabase_service.client.table("quizzes").update({
            "is_active": False,
            "updated_at": ts
        }).eq("id", quiz_id).execute()

        if not result.data:
            raise HTTPException(404, "Quiz not found")

        return {"message": "Quiz deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error deleting quiz: {e}")
