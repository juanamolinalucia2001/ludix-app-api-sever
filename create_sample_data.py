"""
Script para inicializar datos de prueba en Supabase
Ejecutar después de tener usuarios y clases básicas
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from services.supabase_service import supabase_service

async def create_sample_data():
    """Crear datos de muestra para testing"""
    
    try:
        print("🚀 Iniciando creación de datos de prueba...")
        
        # 1. Obtener usuarios existentes
        print("📋 Obteniendo usuarios existentes...")
        users_result = supabase_service.client.table("users").select("*").execute()
        users = users_result.data
        
        if not users:
            print("❌ No hay usuarios en la base de datos. Crea usuarios primero.")
            return
        
        # Separar por roles
        teachers = [u for u in users if u.get("role", "").upper() == "TEACHER"]
        students = [u for u in users if u.get("role", "").upper() == "STUDENT"]
        
        print(f"👩‍🏫 Profesores encontrados: {len(teachers)}")
        print(f"👨‍🎓 Estudiantes encontrados: {len(students)}")
        
        # 2. Obtener clases existentes
        print("🏫 Obteniendo clases existentes...")
        classes_result = supabase_service.client.table("classes").select("*").execute()
        classes = classes_result.data
        
        if not classes:
            print("❌ No hay clases en la base de datos. Crea clases primero.")
            return
        
        print(f"📚 Clases encontradas: {len(classes)}")
        
        # 3. Crear quizzes de ejemplo
        print("🎯 Creando quizzes de ejemplo...")
        
        sample_quizzes = [
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
                        "explanation": "2 + 2 = 4"
                    },
                    {
                        "question_text": "¿Cuánto es 5 × 3?",
                        "options": ["12", "15", "18", "20"],
                        "correct_answer": 1,
                        "explanation": "5 × 3 = 15"
                    },
                    {
                        "question_text": "¿Cuánto es 10 ÷ 2?",
                        "options": ["4", "5", "6", "7"],
                        "correct_answer": 1,
                        "explanation": "10 ÷ 2 = 5"
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
                        "explanation": "Mercurio es el planeta más cercano al Sol"
                    },
                    {
                        "question_text": "¿Qué gas respiramos principalmente?",
                        "options": ["Oxígeno", "Hidrógeno", "Nitrógeno", "Dióxido de carbono"],
                        "correct_answer": 0,
                        "explanation": "Respiramos oxígeno, aunque el aire contiene más nitrógeno"
                    }
                ]
            },
            {
                "title": "Historia Mundial",
                "description": "Eventos importantes de la historia",
                "difficulty": "hard",
                "topic": "Historia",
                "questions": [
                    {
                        "question_text": "¿En qué año comenzó la Segunda Guerra Mundial?",
                        "options": ["1938", "1939", "1940", "1941"],
                        "correct_answer": 1,
                        "explanation": "La Segunda Guerra Mundial comenzó en 1939"
                    }
                ]
            }
        ]
        
        created_quizzes = []
        
        for quiz_data in sample_quizzes:
            for class_obj in classes[:2]:  # Solo para las primeras 2 clases
                for teacher in teachers[:1]:  # Solo el primer profesor
                    
                    print(f"📝 Creando quiz: {quiz_data['title']} para clase {class_obj['name']}")
                    
                    # Crear quiz
                    quiz_id = str(uuid.uuid4())
                    quiz_insert = {
                        "id": quiz_id,
                        "title": quiz_data["title"],
                        "description": quiz_data["description"],
                        "creator_id": teacher["id"],
                        "class_id": class_obj["id"],
                        "difficulty": quiz_data["difficulty"],
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
                        print(f"✅ Quiz creado: {quiz_data['title']}")
                        created_quizzes.append(quiz_result.data[0])
                        
                        # Crear preguntas para este quiz
                        for i, question_data in enumerate(quiz_data["questions"]):
                            question_id = str(uuid.uuid4())
                            question_insert = {
                                "id": question_id,
                                "quiz_id": quiz_id,
                                "question_text": question_data["question_text"],
                                "question_type": "multiple_choice",
                                "options": question_data["options"],
                                "correct_answer": question_data["correct_answer"],
                                "explanation": question_data["explanation"],
                                "difficulty": quiz_data["difficulty"],
                                "points": 10,
                                "time_limit": 30,
                                "order_index": i,
                                "created_at": datetime.utcnow().isoformat()
                            }
                            
                            question_result = supabase_service.client.table("questions").insert(question_insert).execute()
                            
                            if question_result.data:
                                print(f"  ✅ Pregunta creada: {question_data['question_text'][:50]}...")
        
        # 4. Crear sesiones de juego de ejemplo (para estudiantes)
        print("🎮 Creando sesiones de juego de ejemplo...")
        
        for student in students[:3]:  # Solo para los primeros 3 estudiantes
            for quiz in created_quizzes[:2]:  # Solo para los primeros 2 quizzes
                
                # Obtener preguntas del quiz
                questions_result = supabase_service.client.table("questions").select("*").eq("quiz_id", quiz["id"]).execute()
                questions = questions_result.data
                
                if questions:
                    session_id = str(uuid.uuid4())
                    
                    # Simular sesión completada
                    correct_answers = len(questions) // 2  # 50% de aciertos
                    score = (correct_answers / len(questions)) * 100
                    
                    session_insert = {
                        "id": session_id,
                        "student_id": student["id"],
                        "quiz_id": quiz["id"],
                        "status": "completed",
                        "current_question": len(questions),
                        "score": int(score),
                        "total_questions": len(questions),
                        "correct_answers": correct_answers,
                        "incorrect_answers": len(questions) - correct_answers,
                        "start_time": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
                        "end_time": datetime.utcnow().isoformat(),
                        "total_time_seconds": 600,  # 10 minutos
                        "hints_used": 0
                    }
                    
                    session_result = supabase_service.client.table("game_sessions").insert(session_insert).execute()
                    
                    if session_result.data:
                        print(f"🎯 Sesión creada para {student['name']} en quiz {quiz['title']}")
                        
                        # Crear respuestas para esta sesión
                        for j, question in enumerate(questions):
                            answer_id = str(uuid.uuid4())
                            is_correct = j < correct_answers  # Las primeras son correctas
                            selected_answer = question["correct_answer"] if is_correct else (question["correct_answer"] + 1) % len(question["options"])
                            
                            answer_insert = {
                                "id": answer_id,
                                "session_id": session_id,
                                "question_id": question["id"],
                                "selected_answer": selected_answer,
                                "is_correct": is_correct,
                                "time_taken_seconds": 25,
                                "attempts": 1,
                                "hint_used": False,
                                "confidence_level": 80,
                                "answered_at": datetime.utcnow().isoformat()
                            }
                            
                            answer_result = supabase_service.client.table("answers").insert(answer_insert).execute()
                            
                            if answer_result.data:
                                print(f"  ✅ Respuesta creada para pregunta {j+1}")
        
        # 5. Crear métricas de progreso
        print("📊 Creando métricas de progreso...")
        
        for student in students[:3]:
            for class_obj in classes[:1]:  # Solo primera clase
                
                # Calcular métricas basadas en sesiones
                sessions_result = supabase_service.client.table("game_sessions").select("*").eq("student_id", student["id"]).execute()
                sessions = sessions_result.data
                
                if sessions:
                    total_games = len(sessions)
                    total_questions = sum(s.get("total_questions", 0) for s in sessions)
                    total_correct = sum(s.get("correct_answers", 0) for s in sessions)
                    avg_score = sum(s.get("score", 0) for s in sessions) / len(sessions) if sessions else 0
                    best_score = max(s.get("score", 0) for s in sessions) if sessions else 0
                    
                    progress_id = str(uuid.uuid4())
                    progress_insert = {
                        "id": progress_id,
                        "student_id": student["id"],
                        "class_id": class_obj["id"],
                        "total_games_played": total_games,
                        "total_questions_answered": total_questions,
                        "total_correct_answers": total_correct,
                        "total_time_spent_minutes": 30,
                        "average_score": round(avg_score, 2),
                        "best_score": best_score,
                        "current_streak": 2,
                        "longest_streak": 3,
                        "preferred_topics": ["Matemáticas", "Ciencias"],
                        "common_mistakes": ["Operaciones básicas", "Conceptos de física"],
                        "improvement_areas": ["Lectura comprensiva", "Historia"],
                        "last_activity": datetime.utcnow().isoformat(),
                        "weekly_activity_minutes": 120
                    }
                    
                    progress_result = supabase_service.client.table("progress_metrics").insert(progress_insert).execute()
                    
                    if progress_result.data:
                        print(f"📈 Progreso creado para {student['name']}")
        
        print("✅ ¡Datos de prueba creados exitosamente!")
        print("\n📊 Resumen:")
        print(f"- Quizzes creados: {len(created_quizzes)}")
        print(f"- Sesiones de juego simuladas")
        print(f"- Métricas de progreso generadas")
        print(f"- Respuestas de ejemplo creadas")
        
    except Exception as e:
        print(f"❌ Error creando datos de prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_sample_data())
