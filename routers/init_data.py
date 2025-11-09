"""
Router para inicializar datos de prueba en Supabase
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import random

from services.supabase_service import supabase_service
from routers.auth_supabase import get_current_user

router = APIRouter()

class InitDataResponse(BaseModel):
    success: bool
    message: str
    data: dict

@router.post("/sample-data", response_model=InitDataResponse)
async def create_sample_data(current_user: dict = Depends(get_current_user)):
    """Crear datos de muestra para testing (solo profesores)"""
    try:
        if current_user["role"].upper() != "TEACHER":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can initialize sample data"
            )
        
        created_data = {
            "quizzes": 0,
            "questions": 0,
            "sessions": 0,
            "answers": 0,
            "progress": 0
        }
        
        # 1. Obtener clases del profesor actual
        classes_result = supabase_service.client.table("classes").select("*").eq("teacher_id", current_user["id"]).execute()
        classes = classes_result.data
        
        if not classes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You need to create at least one class first"
            )
        
        # 2. Obtener estudiantes de esas clases
        students_result = supabase_service.client.table("users").select("*").eq("role", "STUDENT").execute()
        students = students_result.data
        
        # 3. Datos de quizzes de ejemplo
        sample_quizzes_data = [
            {
                "title": "Matemáticas Básicas",
                "description": "Quiz sobre operaciones matemáticas fundamentales",
                "difficulty": "easy",
                "topic": "Matemáticas",
                "questions": [
                    {
                        "question_text": "¿Cuánto es 2 + 2?",
                        "options": ["3", "4", "5", "6"],
                        "correct_answer": 1,
                        "explanation": "2 + 2 = 4",
                        "points": 10
                    },
                    {
                        "question_text": "¿Cuánto es 5 × 3?",
                        "options": ["12", "15", "18", "20"],
                        "correct_answer": 1,
                        "explanation": "5 × 3 = 15",
                        "points": 15
                    },
                    {
                        "question_text": "¿Cuánto es 10 ÷ 2?",
                        "options": ["4", "5", "6", "7"],
                        "correct_answer": 1,
                        "explanation": "10 ÷ 2 = 5",
                        "points": 10
                    },
                    {
                        "question_text": "¿Cuál es el resultado de 8 - 3?",
                        "options": ["4", "5", "6", "7"],
                        "correct_answer": 1,
                        "explanation": "8 - 3 = 5",
                        "points": 10
                    }
                ]
            },
            {
                "title": "Ciencias Naturales",
                "description": "Conceptos básicos de biología y física",
                "difficulty": "medium",
                "topic": "Ciencias",
                "questions": [
                    {
                        "question_text": "¿Cuál es el planeta más cercano al Sol?",
                        "options": ["Venus", "Mercurio", "Tierra", "Marte"],
                        "correct_answer": 1,
                        "explanation": "Mercurio es el planeta más cercano al Sol",
                        "points": 15
                    },
                    {
                        "question_text": "¿Qué gas respiramos principalmente?",
                        "options": ["Oxígeno", "Hidrógeno", "Nitrógeno", "Dióxido de carbono"],
                        "correct_answer": 0,
                        "explanation": "Respiramos oxígeno, aunque el aire contiene más nitrógeno",
                        "points": 10
                    },
                    {
                        "question_text": "¿Cuántos huesos tiene el cuerpo humano adulto aproximadamente?",
                        "options": ["150", "206", "300", "400"],
                        "correct_answer": 1,
                        "explanation": "El cuerpo humano adulto tiene aproximadamente 206 huesos",
                        "points": 20
                    }
                ]
            },
            {
                "title": "Historia Universal",
                "description": "Eventos importantes de la historia mundial",
                "difficulty": "hard",
                "topic": "Historia",
                "questions": [
                    {
                        "question_text": "¿En qué año comenzó la Segunda Guerra Mundial?",
                        "options": ["1938", "1939", "1940", "1941"],
                        "correct_answer": 1,
                        "explanation": "La Segunda Guerra Mundial comenzó en 1939",
                        "points": 25
                    },
                    {
                        "question_text": "¿Quién fue el primer presidente de Estados Unidos?",
                        "options": ["Thomas Jefferson", "George Washington", "John Adams", "Benjamin Franklin"],
                        "correct_answer": 1,
                        "explanation": "George Washington fue el primer presidente de Estados Unidos",
                        "points": 20
                    }
                ]
            }
        ]
        
        created_quizzes = []
        
        # 4. Crear quizzes para cada clase
        for class_obj in classes:
            for quiz_data in sample_quizzes_data:
                
                # Crear quiz
                quiz_id = str(uuid.uuid4())
                quiz_insert = {
                    "id": quiz_id,
                    "title": f"{quiz_data['title']} - {class_obj['name']}",
                    "description": quiz_data["description"],
                    "creator_id": current_user["id"],
                    "class_id": class_obj["id"],
                    "difficulty": quiz_data["difficulty"].upper(),  # Convertir a mayúsculas
                    "topic": quiz_data["topic"],
                    "is_active": True,
                    "is_published": True,
                    "time_limit": 300,  # 5 minutos
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "published_at": datetime.utcnow().isoformat()
                }
                
                quiz_result = supabase_service.client.table("quizzes").insert(quiz_insert).execute()
                
                if quiz_result.data:
                    created_data["quizzes"] += 1
                    created_quizzes.append(quiz_result.data[0])
                    
                    # Crear preguntas para este quiz
                    for i, question_data in enumerate(quiz_data["questions"]):
                        question_id = str(uuid.uuid4())
                        question_insert = {
                            "id": question_id,
                            "quiz_id": quiz_id,
                            "question_text": question_data["question_text"],
                            "question_type": "MULTIPLE_CHOICE",
                            "options": question_data["options"],
                            "correct_answer": question_data["correct_answer"],
                            "explanation": question_data["explanation"],
                            "difficulty": quiz_data["difficulty"].upper(),  # Convertir a mayúsculas
                            "points": question_data["points"],
                            "time_limit": 30,
                            "order_index": i,
                            "created_at": datetime.utcnow().isoformat()
                        }
                        
                        question_result = supabase_service.client.table("questions").insert(question_insert).execute()
                        
                        if question_result.data:
                            created_data["questions"] += 1
        
        # 5. Crear sesiones de juego simuladas para estudiantes
        if students and created_quizzes:
            for student in students[:5]:  # Primeros 5 estudiantes
                for quiz in created_quizzes[:3]:  # Primeros 3 quizzes
                    
                    # Obtener preguntas del quiz
                    questions_result = supabase_service.client.table("questions").select("*").eq("quiz_id", quiz["id"]).execute()
                    questions = questions_result.data
                    
                    if questions:
                        session_id = str(uuid.uuid4())
                        
                        # Simular sesión completada con resultados variados
                        total_questions = len(questions)
                        correct_answers = random.randint(total_questions // 2, total_questions)
                        score = (correct_answers / total_questions) * 100
                        
                        # Tiempo de inicio aleatorio en los últimos 7 días
                        start_time = datetime.utcnow() - timedelta(days=random.randint(0, 7), hours=random.randint(0, 23))
                        end_time = start_time + timedelta(minutes=random.randint(3, 10))
                        
                        session_insert = {
                            "id": session_id,
                            "student_id": student["id"],
                            "quiz_id": quiz["id"],
                            "status": "COMPLETED",
                            "current_question": total_questions,
                            "score": int(score),
                            "total_questions": total_questions,
                            "correct_answers": correct_answers,
                            "incorrect_answers": total_questions - correct_answers,
                            "start_time": start_time.isoformat(),
                            "end_time": end_time.isoformat(),
                            "total_time_seconds": int((end_time - start_time).total_seconds()),
                            "hints_used": random.randint(0, 2),
                            "created_at": datetime.utcnow().isoformat()
                        }
                        
                        session_result = supabase_service.client.table("game_sessions").insert(session_insert).execute()
                        
                        if session_result.data:
                            created_data["sessions"] += 1
                            
                            # Crear respuestas para esta sesión
                            for j, question in enumerate(questions):
                                answer_id = str(uuid.uuid4())
                                is_correct = j < correct_answers
                                selected_answer = question["correct_answer"] if is_correct else random.choice([i for i in range(len(question["options"])) if i != question["correct_answer"]])
                                
                                answer_insert = {
                                    "id": answer_id,
                                    "session_id": session_id,
                                    "question_id": question["id"],
                                    "selected_answer": selected_answer,
                                    "is_correct": is_correct,
                                    "time_taken_seconds": random.randint(10, 30),
                                    "attempts": 1,
                                    "hint_used": random.choice([True, False]) if random.random() < 0.3 else False,
                                    "confidence_level": random.randint(60, 100),
                                    "answered_at": (start_time + timedelta(seconds=30*j)).isoformat()
                                }
                                
                                answer_result = supabase_service.client.table("answers").insert(answer_insert).execute()
                                
                                if answer_result.data:
                                    created_data["answers"] += 1
            
            # 6. Crear métricas de progreso para estudiantes
            for student in students[:5]:
                for class_obj in classes:
                    
                    # Calcular métricas basadas en sesiones del estudiante
                    sessions_result = supabase_service.client.table("game_sessions").select("*").eq("student_id", student["id"]).execute()
                    student_sessions = sessions_result.data
                    
                    if student_sessions:
                        total_games = len(student_sessions)
                        total_questions = sum(s.get("total_questions", 0) for s in student_sessions)
                        total_correct = sum(s.get("correct_answers", 0) for s in student_sessions)
                        avg_score = sum(s.get("score", 0) for s in student_sessions) / len(student_sessions)
                        best_score = max(s.get("score", 0) for s in student_sessions)
                        total_time = sum(s.get("total_time_seconds", 0) for s in student_sessions) // 60
                        
                        progress_id = str(uuid.uuid4())
                        progress_insert = {
                            "id": progress_id,
                            "student_id": student["id"],
                            "class_id": class_obj["id"],
                            "total_games_played": total_games,
                            "total_questions_answered": total_questions,
                            "total_correct_answers": total_correct,
                            "total_time_spent_minutes": total_time,
                            "average_score": round(avg_score, 2),
                            "best_score": best_score,
                            "current_streak": random.randint(0, 5),
                            "longest_streak": random.randint(2, 8),
                            "preferred_topics": ["Matemáticas", "Ciencias", "Historia"],
                            "common_mistakes": ["Operaciones complejas", "Fechas históricas"],
                            "improvement_areas": ["Velocidad de respuesta", "Comprensión lectora"],
                            "last_activity": datetime.utcnow().isoformat(),
                            "weekly_activity_minutes": random.randint(60, 300),
                            "created_at": datetime.utcnow().isoformat()
                        }
                        
                        progress_result = supabase_service.client.table("progress_metrics").insert(progress_insert).execute()
                        
                        if progress_result.data:
                            created_data["progress"] += 1
        
        return InitDataResponse(
            success=True,
            message="Sample data created successfully",
            data=created_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating sample data: {str(e)}"
        )

@router.get("/status")
async def get_database_status(current_user: dict = Depends(get_current_user)):
    """Obtener estado actual de las tablas"""
    try:
        status = {}
        
        # Contar registros en cada tabla
        tables = ["users", "classes", "quizzes", "questions", "game_sessions", "answers", "progress_metrics"]
        
        for table in tables:
            try:
                result = supabase_service.client.table(table).select("id", count="exact").execute()
                status[table] = result.count if hasattr(result, 'count') else len(result.data or [])
            except Exception as e:
                status[table] = 0
        
        return {
            "success": True,
            "status": status,
            "last_check": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting database status: {str(e)}"
        )

@router.delete("/clear-sample-data")
async def clear_sample_data(current_user: dict = Depends(get_current_user)):
    """Limpiar datos de muestra (solo profesores)"""
    try:
        if current_user["role"].upper() != "TEACHER":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can clear sample data"
            )
        
        # Eliminar en orden inverso por las foreign keys
        tables_to_clear = ["answers", "game_sessions", "progress_metrics", "questions", "quizzes"]
        cleared_data = {}
        
        for table in tables_to_clear:
            try:
                # Solo eliminar datos creados por el profesor actual si es aplicable
                if table == "quizzes":
                    result = supabase_service.client.table(table).delete().eq("creator_id", current_user["id"]).execute()
                else:
                    # Para otras tablas, eliminar todos los registros (cuidado en producción)
                    result = supabase_service.client.table(table).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
                
                cleared_data[table] = len(result.data or [])
            except Exception as e:
                cleared_data[table] = f"Error: {str(e)}"
        
        return {
            "success": True,
            "message": "Sample data cleared",
            "cleared": cleared_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing sample data: {str(e)}"
        )
