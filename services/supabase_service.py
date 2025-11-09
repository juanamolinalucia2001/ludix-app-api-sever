"""
Servicio de base de datos usando exclusivamente Supabase
Sin SQLAlchemy - Solo Supabase client nativo
"""

from typing import List, Dict, Any, Optional
from core.supabase_client import get_supabase_client, get_supabase_admin_client
from supabase import Client
import uuid
from datetime import datetime

class SupabaseService:
    """Servicio para todas las operaciones de base de datos con Supabase"""
    
    def __init__(self):
        self.client: Client = get_supabase_client()
        self.admin_client: Client = get_supabase_admin_client()
    
    # ================================
    # USUARIOS
    # ================================
    
    async def create_user(self, email: str, password: str, name: str, role: str = "student") -> Dict[str, Any]:
        """Crear usuario solo en tabla users (sin Supabase Auth por problema de RLS)"""
        try:
            # Verificar si el usuario ya existe
            existing_user = await self.get_user_by_email(email)
            if existing_user:
                raise Exception("User already exists")
            
            # Crear usuario directamente en tabla users
            user_id = str(uuid.uuid4())
            
            # Hash básico de password (en producción usar bcrypt)
            import hashlib
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            user_data = {
                "id": user_id,
                "email": email,
                "name": name,
                "hashed_password": hashed_password,  # Incluir según tu esquema
                "role": role.upper(),  # ENUM: STUDENT/TEACHER
                "is_active": True
            }
            
            result = self.admin_client.table("users").insert(user_data).execute()
            
            if result.data:
                return {
                    "id": user_id,
                    "email": email,
                    "name": name,
                    "role": role,
                    "is_active": True
                }
            else:
                raise Exception("Failed to create user in database")
                
        except Exception as e:
            raise Exception(f"Error creating user: {str(e)}")
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Obtener usuario por email"""
        try:
            result = self.client.table("users").select("*").eq("email", email).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtener usuario por ID"""
        try:
            result = self.client.table("users").select("*").eq("id", user_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar datos del usuario"""
        try:
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.client.table("users").update(update_data).eq("id", user_id).execute()
            
            if result.data:
                return result.data[0]
            else:
                raise Exception("User not found or update failed")
                
        except Exception as e:
            raise Exception(f"Error updating user: {str(e)}")
    
    # ================================
    # AUTENTICACIÓN
    # ================================
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Autenticar usuario con tabla users (sin Supabase Auth)"""
        try:
            # Buscar usuario por email
            user_data = await self.get_user_by_email(email)
            
            if not user_data:
                return None
            
            # Verificar contraseña hasheada
            import hashlib
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            if user_data.get("hashed_password") == hashed_password:
                return {
                    "id": user_data["id"],
                    "email": user_data["email"],
                    "name": user_data.get("name", ""),
                    "role": user_data.get("role", "STUDENT").lower(),
                    "is_active": user_data.get("is_active", True)
                    # No incluir tokens - se generarán en el endpoint
                }
            
            return None
            
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return None
    
    # ================================
    # CLASES
    # ================================
    
    async def create_class(self, name: str, description: str, teacher_id: str) -> Dict[str, Any]:
        """Crear nueva clase"""
        try:
            class_data = {
                "id": str(uuid.uuid4()),
                "name": name,
                "description": description,
                "teacher_id": teacher_id,
                "class_code": self._generate_class_code(),  # Cambié 'code' por 'class_code'
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("classes").insert(class_data).execute()
            
            if result.data:
                return result.data[0]
            else:
                raise Exception("Failed to create class")
                
        except Exception as e:
            raise Exception(f"Error creating class: {str(e)}")
    
    async def get_teacher_classes(self, teacher_id: str) -> List[Dict[str, Any]]:
        """Obtener clases de un profesor"""
        try:
            result = self.client.table("classes").select("*").eq("teacher_id", teacher_id).eq("is_active", True).execute()
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting teacher classes: {e}")
            return []
    
    def _generate_class_code(self) -> str:
        """Generar código único para clase"""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # ================================
    # QUIZZES/JUEGOS
    # ================================
    
    async def create_quiz(self, title: str, description: str, questions: List[Dict], 
                         class_id: str, created_by: str) -> Dict[str, Any]:
        """Crear un nuevo quiz"""
        try:
            quiz_data = {
                "id": str(uuid.uuid4()),
                "title": title,
                "description": description,
                "creator_id": created_by,  # Cambié 'created_by' por 'creator_id'
                "class_id": class_id,
                "is_active": True,
                "is_published": True,  # Agregué según tu esquema
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("quizzes").insert(quiz_data).execute()
            
            if result.data:
                quiz_id = result.data[0]["id"]
                
                # Crear preguntas por separado
                for i, question in enumerate(questions):
                    question_data = {
                        "id": str(uuid.uuid4()),
                        "quiz_id": quiz_id,
                        "question_text": question.get("question_text", ""),
                        "question_type": question.get("question_type", "multiple_choice"),
                        "options": question.get("options", []),
                        "correct_answer": question.get("correct_answer", 0),
                        "explanation": question.get("explanation"),
                        "difficulty": question.get("difficulty", "medium"),
                        "points": question.get("points", 10),
                        "time_limit": question.get("time_limit", 30),
                        "order_index": i,
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    
                    await self.create_question(question_data)
                
                return result.data[0]
            else:
                raise Exception("Failed to create quiz")
                
        except Exception as e:
            raise Exception(f"Error creating quiz: {str(e)}")
    
    async def get_class_quizzes(self, class_id: str) -> List[Dict[str, Any]]:
        """Obtener quizzes de una clase"""
        try:
            result = self.client.table("quizzes").select("*").eq("class_id", class_id).eq("is_active", True).execute()
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting class quizzes: {e}")
            return []
    
    async def get_quiz_by_id(self, quiz_id: str) -> Optional[Dict[str, Any]]:
        """Obtener quiz por ID con preguntas"""
        try:
            # Obtener quiz con sus preguntas
            quiz_response = self.client.table("quizzes").select("*, questions(*)").eq("id", quiz_id).single().execute()
            return quiz_response.data if quiz_response.data else None
            
        except Exception as e:
            print(f"Error getting quiz by ID: {e}")
            return None

    async def get_game_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtener sesión de juego por ID"""
        try:
            response = self.client.table("game_sessions").select("*").eq("id", session_id).single().execute()
            return response.data if response.data else None
            
        except Exception as e:
            print(f"Error getting game session by ID: {e}")
            return None

    # ================================
    # SESIONES DE JUEGO
    # ================================
    
    async def create_game_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear nueva sesión de juego"""
        try:
            # Obtener información del quiz para total_questions
            quiz = await self.get_quiz_by_id(session_data["quiz_id"])
            total_questions = len(quiz.get("questions", [])) if quiz else 0
            
            game_session = {
                "id": str(uuid.uuid4()),
                "quiz_id": session_data["quiz_id"],
                "student_id": session_data["student_id"],
                "status": session_data.get("status", "in_progress"),
                "current_question": session_data.get("current_question", 0),
                "score": session_data.get("score", 0),
                "total_questions": total_questions,
                "start_time": session_data.get("start_time", datetime.now().isoformat()),
                "correct_answers": 0,
                "incorrect_answers": 0,
                "hints_used": 0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            result = self.client.table("game_sessions").insert(game_session).execute()
            
            if result.data:
                return result.data[0]
            else:
                raise Exception("Failed to create game session")
                
        except Exception as e:
            raise Exception(f"Error creating game session: {str(e)}")
    
    async def update_game_session(self, session_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar sesión de juego"""
        try:
            result = self.client.table("game_sessions").update(update_data).eq("id", session_id).execute()
            
            if result.data:
                return result.data[0]
            else:
                raise Exception("Game session not found or update failed")
                
        except Exception as e:
            raise Exception(f"Error updating game session: {str(e)}")
    
    async def get_student_sessions(self, student_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtener sesiones de un estudiante"""
        try:
            result = (self.client.table("game_sessions")
                     .select("*")
                     .eq("student_id", student_id)
                     .order("created_at", desc=True)
                     .limit(limit)
                     .execute())
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting student sessions: {e}")
            return []
    
    # ================================
    # INSCRIPCIONES
    # ================================
    
    async def enroll_student(self, class_id: str, student_id: str) -> Dict[str, Any]:
        """Inscribir estudiante en clase"""
        try:
            enrollment_data = {
                "id": str(uuid.uuid4()),
                "class_id": class_id,
                "student_id": student_id,
                "enrolled_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("class_enrollments").insert(enrollment_data).execute()
            
            if result.data:
                return result.data[0]
            else:
                raise Exception("Failed to enroll student")
                
        except Exception as e:
            raise Exception(f"Error enrolling student: {str(e)}")
    
    async def get_class_students(self, class_id: str) -> List[Dict[str, Any]]:
        """Obtener estudiantes de una clase"""
        try:
            # Obtener estudiantes que tienen class_id asignado
            result = (self.client.table("users")
                     .select("*")
                     .eq("class_id", class_id)
                     .eq("role", "STUDENT")  # Usar enum en mayúsculas
                     .execute())
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting class students: {e}")
            return []

    # ================================
    # PREGUNTAS
    # ================================
    
    async def create_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear nueva pregunta para un quiz"""
        try:
            question = {
                "id": str(uuid.uuid4()),
                "quiz_id": question_data["quiz_id"],
                "question_text": question_data["question_text"],
                "question_type": question_data.get("question_type", "multiple_choice"),
                "options": question_data["options"],
                "correct_answer": question_data["correct_answer"],
                "explanation": question_data.get("explanation"),
                "difficulty": question_data.get("difficulty", "medium"),
                "points": question_data.get("points", 10),
                "time_limit": question_data.get("time_limit", 30),
                "order_index": question_data.get("order_index", 0),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            result = self.client.table("questions").insert(question).execute()
            
            if result.data:
                return result.data[0]
            else:
                raise Exception("Failed to create question")
                
        except Exception as e:
            raise Exception(f"Error creating question: {str(e)}")

    async def get_quiz_questions(self, quiz_id: str) -> List[Dict[str, Any]]:
        """Obtener preguntas de un quiz"""
        try:
            result = (self.client.table("questions")
                     .select("*")
                     .eq("quiz_id", quiz_id)
                     .order("order_index")
                     .execute())
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting quiz questions: {e}")
            return []

    # ================================
    # RESPUESTAS
    # ================================
    
    async def create_answer(self, answer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear respuesta de estudiante"""
        try:
            answer = {
                "id": str(uuid.uuid4()),
                "session_id": answer_data["session_id"],
                "question_id": answer_data["question_id"],
                "selected_answer": answer_data["selected_answer"],
                "is_correct": answer_data["is_correct"],
                "time_taken_seconds": answer_data["time_taken_seconds"],
                "attempts": answer_data.get("attempts", 1),
                "hint_used": answer_data.get("hint_used", False),
                "confidence_level": answer_data.get("confidence_level"),
                "answered_at": datetime.now().isoformat()
            }
            
            result = self.client.table("answers").insert(answer).execute()
            
            if result.data:
                return result.data[0]
            else:
                raise Exception("Failed to create answer")
                
        except Exception as e:
            raise Exception(f"Error creating answer: {str(e)}")

    async def get_session_answers(self, session_id: str) -> List[Dict[str, Any]]:
        """Obtener respuestas de una sesión"""
        try:
            result = (self.client.table("answers")
                     .select("*")
                     .eq("session_id", session_id)
                     .order("answered_at")
                     .execute())
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting session answers: {e}")
            return []

    # ================================
    # MÉTRICAS Y PROGRESO
    # ================================
    
    async def get_student_progress(self, student_id: str, class_id: str) -> Optional[Dict[str, Any]]:
        """Obtener progreso de un estudiante"""
        try:
            result = (self.client.table("progress_metrics")
                     .select("*")
                     .eq("student_id", student_id)
                     .eq("class_id", class_id)
                     .single()
                     .execute())
            
            return result.data if result.data else None
            
        except Exception as e:
            print(f"Error getting student progress: {e}")
            return None

    async def update_student_progress(self, student_id: str, class_id: str, progress_data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar progreso de estudiante"""
        try:
            # Verificar si existe progreso
            existing = await self.get_student_progress(student_id, class_id)
            
            progress_update = {
                "student_id": student_id,
                "class_id": class_id,
                "last_activity": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                **progress_data
            }
            
            if existing:
                # Actualizar existente
                result = (self.client.table("progress_metrics")
                         .update(progress_update)
                         .eq("student_id", student_id)
                         .eq("class_id", class_id)
                         .execute())
            else:
                # Crear nuevo
                progress_update["id"] = str(uuid.uuid4())
                progress_update["created_at"] = datetime.now().isoformat()
                result = self.client.table("progress_metrics").insert(progress_update).execute()
            
            if result.data:
                return result.data[0]
            else:
                raise Exception("Failed to update student progress")
                
        except Exception as e:
            raise Exception(f"Error updating student progress: {str(e)}")

    # ================================
    # ESTADÍSTICAS PARA DOCENTES
    # ================================
    
    async def get_class_statistics(self, class_id: str) -> Dict[str, Any]:
        """Obtener estadísticas de una clase"""
        try:
            # Contar estudiantes
            students_count = len(await self.get_class_students(class_id))
            
            # Contar quizzes
            quizzes = await self.get_class_quizzes(class_id)
            quizzes_count = len(quizzes)
            
            # Obtener sesiones de juego de la clase
            sessions_result = (self.client.table("game_sessions")
                             .select("*, quizzes!inner(class_id)")
                             .eq("quizzes.class_id", class_id)
                             .execute())
            
            sessions = sessions_result.data if sessions_result.data else []
            total_games_played = len(sessions)
            
            # Calcular estadísticas
            total_score = sum(session.get("score", 0) for session in sessions)
            average_score = total_score / total_games_played if total_games_played > 0 else 0
            
            return {
                "students_count": students_count,
                "quizzes_count": quizzes_count,
                "total_games_played": total_games_played,
                "average_score": round(average_score, 2),
                "active_students": students_count  # Placeholder
            }
            
        except Exception as e:
            print(f"Error getting class statistics: {e}")
            return {
                "students_count": 0,
                "quizzes_count": 0,
                "total_games_played": 0,
                "average_score": 0,
                "active_students": 0
            }

    async def get_student_results_in_class(self, class_id: str) -> List[Dict[str, Any]]:
        """Obtener resultados de todos los estudiantes en una clase"""
        try:
            # Obtener estudiantes de la clase
            students = await self.get_class_students(class_id)
            
            results = []
            for student in students:
                # Obtener sesiones del estudiante en esta clase
                sessions_result = (self.client.table("game_sessions")
                                 .select("*, quizzes!inner(class_id, title)")
                                 .eq("student_id", student["id"])
                                 .eq("quizzes.class_id", class_id)
                                 .execute())
                
                sessions = sessions_result.data if sessions_result.data else []
                
                # Calcular estadísticas del estudiante
                total_games = len(sessions)
                total_score = sum(session.get("score", 0) for session in sessions)
                average_score = total_score / total_games if total_games > 0 else 0
                best_score = max((session.get("score", 0) for session in sessions), default=0)
                
                results.append({
                    "student": student,
                    "total_games": total_games,
                    "average_score": round(average_score, 2),
                    "best_score": best_score,
                    "last_activity": sessions[-1].get("start_time") if sessions else None
                })
            
            return results
            
        except Exception as e:
            print(f"Error getting student results: {e}")
            return []

    # ================================
    # UTILIDADES
    # ================================
    
    async def join_class_by_code(self, student_id: str, class_code: str) -> Dict[str, Any]:
        """Unir estudiante a clase por código"""
        try:
            # Buscar clase por código
            class_result = (self.client.table("classes")
                           .select("*")
                           .eq("class_code", class_code)
                           .eq("is_active", True)
                           .single()
                           .execute())
            
            if not class_result.data:
                raise Exception("Class not found or inactive")
            
            class_data = class_result.data
            
            # Actualizar estudiante con class_id
            update_result = (self.client.table("users")
                           .update({"class_id": class_data["id"], "updated_at": datetime.now().isoformat()})
                           .eq("id", student_id)
                           .execute())
            
            if update_result.data:
                return {
                    "message": "Successfully joined class",
                    "class": class_data,
                    "student_updated": True
                }
            else:
                raise Exception("Failed to update student")
                
        except Exception as e:
            raise Exception(f"Error joining class: {str(e)}")

# Instancia global del servicio
supabase_service = SupabaseService()
