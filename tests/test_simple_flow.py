"""
Test simplificado del flujo completo de Ludix
Prueba todos los endpoints principales con casos reales
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid
from datetime import datetime

class TestLudixRealFlow:
    """Tests del flujo completo simplificado"""
    
    def test_teacher_endpoints_flow(self, client: TestClient, mock_supabase_service):
        """Test del flujo de docente: crear aula, quiz, ver estadísticas"""
        
        print("\n👨‍🏫 === FLUJO DE DOCENTE ===")
        
        # Crear token de docente
        from routers.auth_supabase import create_access_token
        teacher_id = str(uuid.uuid4())
        teacher_token = create_access_token({
            "sub": teacher_id,
            "email": "teacher@test.com", 
            "role": "teacher"
        })
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        # Mock usuario docente
        mock_supabase_service.get_user_by_id.return_value = {
            "id": teacher_id,
            "email": "teacher@test.com",
            "name": "Test Teacher",
            "role": "teacher",
            "is_active": True
        }
        
        # 1. Crear aula
        class_data = {
            "name": "Matemáticas 101",
            "description": "Curso básico de matemáticas"
        }
        
        mock_class_id = str(uuid.uuid4())
        mock_supabase_service.create_class.return_value = {
            "id": mock_class_id,
            "name": class_data["name"],
            "description": class_data["description"],
            "teacher_id": teacher_id,
            "class_code": "MATH101",
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        
        response = client.post("/classes/", json=class_data, headers=headers)
        print(f"✅ Crear aula: {response.status_code}")
        
        # 2. Ver mis aulas
        mock_supabase_service.get_teacher_classes.return_value = [
            {
                "id": mock_class_id,
                "name": "Matemáticas 101",
                "class_code": "MATH101",
                "teacher_id": teacher_id,
                "is_active": True,
                "created_at": datetime.now().isoformat()
            }
        ]
        
        response = client.get("/classes/my-classes", headers=headers)
        print(f"✅ Ver mis aulas: {response.status_code}")
        
        # 3. Ver estadísticas del aula
        mock_supabase_service.get_class_statistics.return_value = {
            "students_count": 5,
            "quizzes_count": 2,
            "total_games_played": 10,
            "average_score": 85.0,
            "active_students": 4
        }
        
        response = client.get(f"/classes/{mock_class_id}/statistics", headers=headers)
        print(f"✅ Ver estadísticas: {response.status_code}")
        
        # 4. Crear quiz
        quiz_data = {
            "title": "Quiz de Álgebra",
            "description": "Evaluación básica",
            "class_id": mock_class_id,
            "questions": [
                {
                    "question_text": "¿Cuánto es 2 + 2?",
                    "options": ["3", "4", "5", "6"],
                    "correct_answer": 1,
                    "points": 10
                }
            ]
        }
        
        mock_quiz_id = str(uuid.uuid4())
        mock_supabase_service.create_quiz.return_value = {
            "id": mock_quiz_id,
            "title": quiz_data["title"],
            "class_id": mock_class_id,
            "creator_id": teacher_id,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        
        mock_supabase_service.create_question.return_value = {
            "id": str(uuid.uuid4()),
            "quiz_id": mock_quiz_id,
            "question_text": "¿Cuánto es 2 + 2?",
            "options": ["3", "4", "5", "6"],
            "correct_answer": 1,
            "points": 10
        }
        
        response = client.post("/quizzes/", json=quiz_data, headers=headers)
        print(f"✅ Crear quiz: {response.status_code}")
        
        print("🎉 FLUJO DE DOCENTE COMPLETADO")
        
    def test_student_endpoints_flow(self, client: TestClient, mock_supabase_service):
        """Test del flujo de estudiante: setup perfil, unirse a aula, jugar"""
        
        print("\n🎒 === FLUJO DE ESTUDIANTE ===")
        
        # Crear token de estudiante  
        from routers.auth_supabase import create_access_token
        student_id = str(uuid.uuid4())
        class_id = str(uuid.uuid4())
        
        student_token = create_access_token({
            "sub": student_id,
            "email": "student@test.com",
            "role": "student"
        })
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # Mock usuario estudiante
        mock_supabase_service.get_user_by_id.return_value = {
            "id": student_id,
            "email": "student@test.com", 
            "name": "Test Student",
            "role": "student",
            "is_active": True,
            "class_id": class_id
        }
        
        # 1. Ver avatares disponibles
        response = client.get("/users/available-avatars", headers=headers)
        print(f"✅ Ver avatares: {response.status_code}")
        assert response.status_code == 200
        
        # 2. Ver mascotas disponibles
        response = client.get("/users/available-mascots", headers=headers)
        print(f"✅ Ver mascotas: {response.status_code}")
        assert response.status_code == 200
        
        # 3. Configurar perfil
        profile_data = {
            "name": "Ana García",
            "avatar_url": "/avatars/avatar1.png",
            "mascot": "gato"
        }
        
        mock_supabase_service.update_user.return_value = {
            "id": student_id,
            "email": "student@test.com",
            "name": profile_data["name"],
            "role": "student",
            "avatar_url": profile_data["avatar_url"],
            "mascot": profile_data["mascot"],
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        
        response = client.post("/users/setup-profile", json=profile_data, headers=headers)
        print(f"✅ Setup perfil: {response.status_code}")
        
        # 4. Unirse a aula
        join_data = {"class_code": "MATH101"}
        
        mock_supabase_service.join_class_by_code.return_value = {
            "message": "Successfully joined class",
            "class": {
                "id": class_id,
                "name": "Matemáticas 101",
                "class_code": "MATH101"
            }
        }
        
        response = client.post("/classes/join", json=join_data, headers=headers)
        print(f"✅ Unirse a aula: {response.status_code}")
        
        # 5. Ver juegos disponibles
        mock_supabase_service.get_class_quizzes.return_value = [
            {
                "id": str(uuid.uuid4()),
                "title": "Quiz de Álgebra", 
                "is_published": True,
                "is_active": True,
                "difficulty": "easy",
                "created_at": datetime.now().isoformat()
            }
        ]
        
        mock_supabase_service.get_quiz_questions.return_value = [{"points": 10}]
        
        response = client.get("/games/", headers=headers)
        print(f"✅ Ver juegos: {response.status_code}")
        
        # 6. Crear sesión de juego
        quiz_id = str(uuid.uuid4())
        session_data = {"quiz_id": quiz_id}
        
        mock_supabase_service.get_quiz_by_id.return_value = {
            "id": quiz_id,
            "title": "Quiz Test",
            "questions": [{"points": 10}, {"points": 10}]
        }
        
        mock_supabase_service.create_game_session.return_value = {
            "id": str(uuid.uuid4()),
            "quiz_id": quiz_id,
            "student_id": student_id,
            "status": "in_progress",
            "current_question": 0,
            "score": 0,
            "total_questions": 2,
            "start_time": datetime.now().isoformat()
        }
        
        response = client.post("/games/session", json=session_data, headers=headers)
        print(f"✅ Crear sesión: {response.status_code}")
        
        print("🎉 FLUJO DE ESTUDIANTE COMPLETADO")
        
    def test_role_access_control(self, client: TestClient, mock_supabase_service):
        """Test de control de acceso por roles"""
        
        print("\n🔒 === CONTROL DE ACCESO ===")
        
        from routers.auth_supabase import create_access_token
        
        teacher_id = str(uuid.uuid4())
        student_id = str(uuid.uuid4())
        class_id = str(uuid.uuid4())
        
        teacher_token = create_access_token({
            "sub": teacher_id,
            "email": "teacher@test.com",
            "role": "teacher"
        })
        
        student_token = create_access_token({
            "sub": student_id, 
            "email": "student@test.com",
            "role": "student"
        })
        
        teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
        student_headers = {"Authorization": f"Bearer {student_token}"}
        
        # Mock users
        def mock_get_user(user_id):
            if user_id == teacher_id:
                return {
                    "id": teacher_id,
                    "role": "teacher",
                    "email": "teacher@test.com",
                    "name": "Teacher",
                    "is_active": True
                }
            else:
                return {
                    "id": student_id,
                    "role": "student", 
                    "email": "student@test.com",
                    "name": "Student",
                    "is_active": True,
                    "class_id": class_id
                }
        
        mock_supabase_service.get_user_by_id.side_effect = mock_get_user
        
        # Estudiante NO puede crear aulas
        class_data = {"name": "Test Class"}
        response = client.post("/classes/", json=class_data, headers=student_headers)
        print(f"🚫 Estudiante crear aula (debe fallar): {response.status_code}")
        assert response.status_code == 403
        
        # Docente NO puede crear sesiones de juego  
        session_data = {"quiz_id": str(uuid.uuid4())}
        response = client.post("/games/session", json=session_data, headers=teacher_headers)
        print(f"🚫 Docente crear sesión (debe fallar): {response.status_code}")
        assert response.status_code == 403
        
        # Estudiante NO puede ver estadísticas
        response = client.get(f"/classes/{class_id}/statistics", headers=student_headers)
        print(f"🚫 Estudiante ver stats (debe fallar): {response.status_code}")
        assert response.status_code == 403
        
        print("✅ Control de acceso funcionando correctamente")
        print("🎉 TESTS DE CONTROL COMPLETADOS")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
