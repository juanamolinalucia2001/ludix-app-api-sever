"""
Router de juegos usando exclusivamente Supabase
Versión pura sin SQLAlchemy - Solo Supabase client nativo
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from services.supabase_service import supabase_service
from routers.auth_supabase import get_current_user

router = APIRouter()

# Pydantic models
class GameSessionCreate(BaseModel):
    quiz_id: str

class AnswerSubmit(BaseModel):
    question_id: str
    selected_answer: int
    time_taken_seconds: int
    hint_used: bool = False
    confidence_level: Optional[int] = None

class GameSessionResponse(BaseModel):
    id: str
    quiz_id: str
    status: str
    current_question: int
    score: int
    total_questions: int
    start_time: str
    quiz_title: str

class GameInfo(BaseModel):
    id: str
    title: str
    description: str
    questions_count: int
    max_score: int
    is_active: bool
    created_at: str

@router.get("/", response_model=List[GameInfo])
async def get_available_games(current_user: dict = Depends(get_current_user)):
    """Get available games/quizzes for the current student"""
    try:
        # Verificar que el usuario sea estudiante
        if current_user["role"].upper() != "STUDENT":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can access games"
            )
        
        # Verificar que el estudiante esté en una clase
        if not current_user.get("class_id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student must be enrolled in a class"
            )
        
        # Obtener quizzes de la clase del estudiante
        quizzes = await supabase_service.get_class_quizzes(current_user["class_id"])
        
        games = []
        for quiz in quizzes:
            if quiz.get("is_active", True):
                games.append(GameInfo(
                    id=quiz["id"],
                    title=quiz["title"],
                    description=quiz.get("description", ""),
                    questions_count=len(quiz.get("questions", [])),
                    max_score=sum(q.get("points", 10) for q in quiz.get("questions", [])),
                    is_active=quiz.get("is_active", True),
                    created_at=quiz.get("created_at", "")
                ))
        
        return games
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting available games: {str(e)}"
        )

@router.post("/session", response_model=GameSessionResponse)
async def create_game_session(
    session_data: GameSessionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new game session for a quiz"""
    try:
        # Verificar que el usuario sea estudiante
        if current_user["role"].upper() != "STUDENT":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can create game sessions"
            )
        
        # Crear nueva sesión de juego
        session = await supabase_service.create_game_session({
            "student_id": current_user["id"],
            "quiz_id": session_data.quiz_id,
            "status": "in_progress",
            "current_question": 0,
            "score": 0,
            "answers": [],
            "start_time": datetime.now().isoformat()
        })
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create game session"
            )
        
        # Obtener información del quiz para la respuesta
        quiz = await supabase_service.get_quiz_by_id(session_data.quiz_id)
        
        return GameSessionResponse(
            id=session["id"],
            quiz_id=session["quiz_id"],
            status=session["status"],
            current_question=session["current_question"],
            score=session["score"],
            total_questions=len(quiz.get("questions", [])) if quiz else 0,
            start_time=session["start_time"],
            quiz_title=quiz.get("title", "Unknown Quiz") if quiz else "Unknown Quiz"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating game session: {str(e)}"
        )

@router.get("/session/{session_id}")
async def get_game_session(
    session_id: str, 
    current_user: dict = Depends(get_current_user)
):
    """Get current game session information"""
    try:
        # Obtener sesión de juego
        session = await supabase_service.get_game_session_by_id(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game session not found"
            )
        
        # Verificar que la sesión pertenece al usuario actual
        if session["student_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own game sessions"
            )
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting game session: {str(e)}"
        )

@router.post("/session/{session_id}/answer")
async def submit_answer(
    session_id: str,
    answer: AnswerSubmit,
    current_user: dict = Depends(get_current_user)
):
    """Submit an answer for the current question"""
    try:
        # Obtener sesión de juego
        session = await supabase_service.get_game_session_by_id(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game session not found"
            )
        
        # Verificar que la sesión pertenece al usuario actual
        if session["student_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own game sessions"
            )
        
        # Verificar que la sesión esté activa
        if session["status"] != "in_progress":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game session is not active"
            )
        
        # Obtener la pregunta para verificar respuesta correcta
        question_result = supabase_service.client.table("questions").select("*").eq("id", answer.question_id).single().execute()
        
        if not question_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        question = question_result.data
        is_correct = answer.selected_answer == question["correct_answer"]
        points_earned = question["points"] if is_correct else 0
        
        # Crear registro de respuesta
        answer_data = {
            "session_id": session_id,
            "question_id": answer.question_id,
            "selected_answer": answer.selected_answer,
            "is_correct": is_correct,
            "time_taken_seconds": answer.time_taken_seconds,
            "hint_used": answer.hint_used,
            "confidence_level": answer.confidence_level
        }
        
        await supabase_service.create_answer(answer_data)
        
        # Actualizar sesión
        current_question = session["current_question"] + 1
        new_score = session["score"] + points_earned
        correct_answers = session.get("correct_answers", 0) + (1 if is_correct else 0)
        incorrect_answers = session.get("incorrect_answers", 0) + (0 if is_correct else 1)
        hints_used = session.get("hints_used", 0) + (1 if answer.hint_used else 0)
        
        # Verificar si es la última pregunta
        total_questions = session["total_questions"]
        session_status = "completed" if current_question >= total_questions else "in_progress"
        
        update_data = {
            "current_question": current_question,
            "score": new_score,
            "correct_answers": correct_answers,
            "incorrect_answers": incorrect_answers,
            "hints_used": hints_used,
            "status": session_status,
            "updated_at": supabase_service.client.functions.invoke("now")
        }
        
        if session_status == "completed":
            update_data["end_time"] = supabase_service.client.functions.invoke("now")
        
        await supabase_service.update_game_session(session_id, update_data)
        
        return {
            "message": "Answer submitted successfully",
            "correct": is_correct,
            "correct_answer": question["correct_answer"] if is_correct else None,
            "explanation": question.get("explanation") if is_correct else None,
            "points_earned": points_earned,
            "current_score": new_score,
            "next_question": current_question,
            "session_completed": session_status == "completed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting answer: {str(e)}"
        )

@router.get("/sessions", response_model=List[dict])
async def get_student_sessions(current_user: dict = Depends(get_current_user)):
    """Get all game sessions for the current student"""
    try:
        if current_user["role"].upper() != "STUDENT":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can access game sessions"
            )
        
        sessions = await supabase_service.get_student_sessions(current_user["id"])
        return sessions or []
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting student sessions: {str(e)}"
        )
