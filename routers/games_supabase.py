"""
Router de juegos usando exclusivamente Supabase
Versión pura sin SQLAlchemy - Solo Supabase client nativo
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone

from services.supabase_service import supabase_service
from routers.auth_supabase import get_current_user

router = APIRouter()

# ===========================
# Modelos Pydantic
# ===========================

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


# ===========================
# Endpoints
# ===========================

@router.get("/", response_model=List[GameInfo])
async def get_available_games(current_user: dict = Depends(get_current_user)):
    """Lista de quizzes disponibles para el alumno actual."""
    try:
        if current_user["role"].upper() != "STUDENT":
            raise HTTPException(status_code=403, detail="Only students can access games")

        if not current_user.get("class_id"):
            raise HTTPException(status_code=400, detail="Student must be enrolled in a class")

        quizzes = await supabase_service.get_class_quizzes(current_user["class_id"]) or []

        items: List[GameInfo] = []
        for qz in quizzes:
            # Contar preguntas de cada quiz
            qs = supabase_service.client.table("questions").select("id").eq("quiz_id", qz["id"]).execute()
            count_q = len(qs.data or [])
            max_score = 0
            if qs.data:
                # Si querés sumar puntos reales, pedí points también; para simplicidad 10 por pregunta
                max_score = count_q * 10

            items.append(GameInfo(
                id=qz["id"],
                title=qz["title"],
                description=qz.get("description") or "",
                questions_count=count_q,
                max_score=max_score,
                is_active=qz.get("is_active", True),
                created_at=qz.get("created_at", ""),
            ))

        return items

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting available games: {e}")


@router.post("/session", response_model=GameSessionResponse)
async def create_game_session(
    session_data: GameSessionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Crea una nueva sesión de juego para un quiz."""
    if current_user["role"].upper() != "STUDENT":
        raise HTTPException(status_code=403, detail="Only students can create game sessions")

    # Total de preguntas del quiz (para controlar el avance)
    qs = supabase_service.client.table("questions").select("id").eq("quiz_id", session_data.quiz_id).execute()
    total_q = len(qs.data or [])

    ts = datetime.now(timezone.utc).isoformat()

    try:
        # Insert respetando enums en MAYÚSCULAS
        ins = supabase_service.client.table("game_sessions").insert({
            "student_id": current_user["id"],
            "quiz_id": session_data.quiz_id,
            "status": "IN_PROGRESS",        # <--- ENUM MAYÚSCULAS
            "current_question": 0,
            "score": 0,
            "correct_answers": 0,
            "incorrect_answers": 0,
            "hints_used": 0,
            "total_questions": total_q,
            "is_active": True,              # requiere columna is_active (boolean)
            "start_time": ts,
            "created_at": ts,
            "updated_at": ts,
        }).execute()

        if not ins.data:
            raise HTTPException(status_code=400, detail="Failed to create game session")

        sess = ins.data[0]
        quiz = await supabase_service.get_quiz_by_id(session_data.quiz_id) or {}

        return GameSessionResponse(
            id=sess["id"],
            quiz_id=sess["quiz_id"],
            status=sess["status"],
            current_question=sess["current_question"],
            score=sess["score"],
            total_questions=sess.get("total_questions", total_q),
            start_time=sess.get("start_time", ts),
            quiz_title=quiz.get("title", "Unknown Quiz"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating game session: {e}")


@router.get("/session/{session_id}")
async def get_game_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Devuelve el estado actual de una sesión de juego."""
    try:
        res = supabase_service.client.table("game_sessions").select("*").eq("id", session_id).single().execute()
        session = res.data
        if not session:
            raise HTTPException(status_code=404, detail="Game session not found")

        if session["student_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="You can only access your own game sessions")

        return session

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting game session: {e}")


@router.post("/session/{session_id}/answer")
async def submit_answer(
    session_id: str,
    answer: AnswerSubmit,
    current_user: dict = Depends(get_current_user)
):
    """Registra la respuesta del alumno para la pregunta actual."""
    try:
        # Traer sesión
        sres = supabase_service.client.table("game_sessions").select("*").eq("id", session_id).single().execute()
        session = sres.data
        if not session:
            raise HTTPException(status_code=404, detail="Game session not found")

        if session["student_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="You can only access your own game sessions")

        # Estado debe ser IN_PROGRESS (enum)
        if session["status"] != "IN_PROGRESS":
            raise HTTPException(status_code=400, detail="Game session is not active")

        # Traer pregunta y evaluar
        qres = supabase_service.client.table("questions").select("*").eq("id", answer.question_id).single().execute()
        if not qres.data:
            raise HTTPException(status_code=404, detail="Question not found")

        q = qres.data
        is_correct = (answer.selected_answer == q["correct_answer"])
        points = q.get("points", 0) if is_correct else 0

        # Guardar answer (si existe tabla answers y servicio)
        await supabase_service.create_answer({
            "session_id": session_id,
            "question_id": answer.question_id,
            "selected_answer": answer.selected_answer,
            "is_correct": is_correct,
            "time_taken_seconds": answer.time_taken_seconds,
            "hint_used": answer.hint_used,
            "confidence_level": answer.confidence_level
        })

        # Avanzar sesión
        current_q = (session.get("current_question") or 0) + 1
        total_q = session.get("total_questions") or 0
        done = (total_q > 0 and current_q >= total_q)
        new_status = "COMPLETED" if done else "IN_PROGRESS"

        ts = datetime.now(timezone.utc).isoformat()
        upd = {
            "current_question": current_q,
            "score": (session.get("score") or 0) + points,
            "correct_answers": (session.get("correct_answers") or 0) + (1 if is_correct else 0),
            "incorrect_answers": (session.get("incorrect_answers") or 0) + (0 if is_correct else 1),
            "hints_used": (session.get("hints_used") or 0) + (1 if answer.hint_used else 0),
            "status": new_status,                # <--- ENUM MAYÚSCULAS
            "updated_at": ts,
        }
        if done:
            upd["end_time"] = ts
            upd["is_active"] = False

        supabase_service.client.table("game_sessions").update(upd).eq("id", session_id).execute()

        return {
            "message": "Answer submitted successfully",
            "correct": is_correct,
            "correct_answer": q["correct_answer"] if is_correct else None,
            "explanation": q.get("explanation") if is_correct else None,
            "points_earned": points,
            "current_score": upd["score"],
            "next_question": current_q,
            "session_completed": done,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting answer: {e}")


@router.get("/sessions", response_model=List[dict])
async def get_student_sessions(current_user: dict = Depends(get_current_user)):
    """Lista todas las sesiones de juego del alumno actual."""
    try:
        if current_user["role"].upper() != "STUDENT":
            raise HTTPException(status_code=403, detail="Only students can access game sessions")

        res = supabase_service.client.table("game_sessions").select("*").eq("student_id", current_user["id"]).execute()
        return res.data or []

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting student sessions: {e}")
"""
Router de juegos usando exclusivamente Supabase
Versión pura sin SQLAlchemy - Solo Supabase client nativo
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone

from services.supabase_service import supabase_service
from routers.auth_supabase import get_current_user

router = APIRouter()

# ===========================
# Modelos Pydantic
# ===========================

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


# ===========================
# Endpoints
# ===========================

@router.get("/", response_model=List[GameInfo])
async def get_available_games(current_user: dict = Depends(get_current_user)):
    """Lista de quizzes disponibles para el alumno actual."""
    try:
        if current_user["role"].upper() != "STUDENT":
            raise HTTPException(status_code=403, detail="Only students can access games")

        if not current_user.get("class_id"):
            raise HTTPException(status_code=400, detail="Student must be enrolled in a class")

        quizzes = await supabase_service.get_class_quizzes(current_user["class_id"]) or []

        items: List[GameInfo] = []
        for qz in quizzes:
            # Contar preguntas de cada quiz
            qs = supabase_service.client.table("questions").select("id").eq("quiz_id", qz["id"]).execute()
            count_q = len(qs.data or [])
            max_score = 0
            if qs.data:
                # Si querés sumar puntos reales, pedí points también; para simplicidad 10 por pregunta
                max_score = count_q * 10

            items.append(GameInfo(
                id=qz["id"],
                title=qz["title"],
                description=qz.get("description") or "",
                questions_count=count_q,
                max_score=max_score,
                is_active=qz.get("is_active", True),
                created_at=qz.get("created_at", ""),
            ))

        return items

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting available games: {e}")


@router.post("/session", response_model=GameSessionResponse)
async def create_game_session(
    session_data: GameSessionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Crea una nueva sesión de juego para un quiz."""
    if current_user["role"].upper() != "STUDENT":
        raise HTTPException(status_code=403, detail="Only students can create game sessions")

    # Total de preguntas del quiz (para controlar el avance)
    qs = supabase_service.client.table("questions").select("id").eq("quiz_id", session_data.quiz_id).execute()
    total_q = len(qs.data or [])

    ts = datetime.now(timezone.utc).isoformat()

    try:
        # Insert respetando enums en MAYÚSCULAS
        ins = supabase_service.client.table("game_sessions").insert({
            "student_id": current_user["id"],
            "quiz_id": session_data.quiz_id,
            "status": "IN_PROGRESS",        # <--- ENUM MAYÚSCULAS
            "current_question": 0,
            "score": 0,
            "correct_answers": 0,
            "incorrect_answers": 0,
            "hints_used": 0,
            "total_questions": total_q,
            "is_active": True,              # requiere columna is_active (boolean)
            "start_time": ts,
            "created_at": ts,
            "updated_at": ts,
        }).execute()

        if not ins.data:
            raise HTTPException(status_code=400, detail="Failed to create game session")

        sess = ins.data[0]
        quiz = await supabase_service.get_quiz_by_id(session_data.quiz_id) or {}

        return GameSessionResponse(
            id=sess["id"],
            quiz_id=sess["quiz_id"],
            status=sess["status"],
            current_question=sess["current_question"],
            score=sess["score"],
            total_questions=sess.get("total_questions", total_q),
            start_time=sess.get("start_time", ts),
            quiz_title=quiz.get("title", "Unknown Quiz"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating game session: {e}")


@router.get("/session/{session_id}")
async def get_game_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Devuelve el estado actual de una sesión de juego."""
    try:
        res = supabase_service.client.table("game_sessions").select("*").eq("id", session_id).single().execute()
        session = res.data
        if not session:
            raise HTTPException(status_code=404, detail="Game session not found")

        if session["student_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="You can only access your own game sessions")

        return session

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting game session: {e}")


@router.post("/session/{session_id}/answer")
async def submit_answer(
    session_id: str,
    answer: AnswerSubmit,
    current_user: dict = Depends(get_current_user)
):
    """Registra la respuesta del alumno para la pregunta actual."""
    try:
        # Traer sesión
        sres = supabase_service.client.table("game_sessions").select("*").eq("id", session_id).single().execute()
        session = sres.data
        if not session:
            raise HTTPException(status_code=404, detail="Game session not found")

        if session["student_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="You can only access your own game sessions")

        # Estado debe ser IN_PROGRESS (enum)
        if session["status"] != "IN_PROGRESS":
            raise HTTPException(status_code=400, detail="Game session is not active")

        # Traer pregunta y evaluar
        qres = supabase_service.client.table("questions").select("*").eq("id", answer.question_id).single().execute()
        if not qres.data:
            raise HTTPException(status_code=404, detail="Question not found")

        q = qres.data
        is_correct = (answer.selected_answer == q["correct_answer"])
        points = q.get("points", 0) if is_correct else 0

        # Guardar answer (si existe tabla answers y servicio)
        await supabase_service.create_answer({
            "session_id": session_id,
            "question_id": answer.question_id,
            "selected_answer": answer.selected_answer,
            "is_correct": is_correct,
            "time_taken_seconds": answer.time_taken_seconds,
            "hint_used": answer.hint_used,
            "confidence_level": answer.confidence_level
        })

        # Avanzar sesión
        current_q = (session.get("current_question") or 0) + 1
        total_q = session.get("total_questions") or 0
        done = (total_q > 0 and current_q >= total_q)
        new_status = "COMPLETED" if done else "IN_PROGRESS"

        ts = datetime.now(timezone.utc).isoformat()
        upd = {
            "current_question": current_q,
            "score": (session.get("score") or 0) + points,
            "correct_answers": (session.get("correct_answers") or 0) + (1 if is_correct else 0),
            "incorrect_answers": (session.get("incorrect_answers") or 0) + (0 if is_correct else 1),
            "hints_used": (session.get("hints_used") or 0) + (1 if answer.hint_used else 0),
            "status": new_status,                # <--- ENUM MAYÚSCULAS
            "updated_at": ts,
        }
        if done:
            upd["end_time"] = ts
            upd["is_active"] = False

        supabase_service.client.table("game_sessions").update(upd).eq("id", session_id).execute()

        return {
            "message": "Answer submitted successfully",
            "correct": is_correct,
            "correct_answer": q["correct_answer"] if is_correct else None,
            "explanation": q.get("explanation") if is_correct else None,
            "points_earned": points,
            "current_score": upd["score"],
            "next_question": current_q,
            "session_completed": done,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting answer: {e}")


@router.get("/sessions", response_model=List[dict])
async def get_student_sessions(current_user: dict = Depends(get_current_user)):
    """Lista todas las sesiones de juego del alumno actual."""
    try:
        if current_user["role"].upper() != "STUDENT":
            raise HTTPException(status_code=403, detail="Only students can access game sessions")

        res = supabase_service.client.table("game_sessions").select("*").eq("student_id", current_user["id"]).execute()
        return res.data or []

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting student sessions: {e}")
