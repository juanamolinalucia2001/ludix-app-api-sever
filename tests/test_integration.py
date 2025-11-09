"""
Tests de integración para flujos completos de la aplicación
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.User import User, UserRole
from models.Quiz import Quiz, Class
from tests.conftest import assert_valid_token_response, assert_user_data


class TestCompleteUserFlow:
    """Test de flujo completo de usuario desde registro hasta juego"""
    
    def test_complete_student_flow(self, client: TestClient, db_session: Session, 
                                 test_teacher: User, test_class: Class, test_quiz: Quiz):
        """Test flujo completo: registro de estudiante -> inscripción -> juego"""
        
        # 1. Registro de estudiante
        student_data = {
            "email": "integration_student@ludix.com",
            "password": "student123",
            "name": "Integration Student",
            "role": "student"
        }
        
        register_response = client.post("/auth/register", json=student_data)
        assert register_response.status_code == 200
        
        register_data = register_response.json()
        assert_valid_token_response(register_data)
        
        student_token = register_data["access_token"]
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # 2. Verificar perfil del estudiante
        profile_response = client.get("/users/profile", headers=headers)
        assert profile_response.status_code == 200
        
        profile_data = profile_response.json()
        assert_user_data(profile_data, student_data["email"], "student")
        assert profile_data["class_id"] is None  # No inscrito aún
        
        # 3. Simular inscripción en clase (normalmente se haría por código de clase)
        student = db_session.query(User).filter(User.email == student_data["email"]).first()
        student.class_id = test_class.id
        db_session.commit()
        
        # 4. Verificar que ahora puede ver juegos disponibles
        games_response = client.get("/games/", headers=headers)
        assert games_response.status_code == 200
        
        games = games_response.json()
        assert len(games) >= 1
        assert games[0]["id"] == str(test_quiz.id)
        
        # 5. Iniciar sesión de juego
        start_response = client.post(f"/games/{test_quiz.id}/start", headers=headers)
        assert start_response.status_code == 200
        
        session_data = start_response.json()
        session_id = session_data["id"]
        assert session_data["status"] == "in_progress"
        
        # 6. Jugar - responder todas las preguntas
        current_score = 0
        for i, question in enumerate(test_quiz.questions):
            answer_data = {
                "question_id": str(question.id),
                "selected_answer": question.correct_answer,
                "time_taken_seconds": 20,
                "hint_used": False
            }
            
            answer_response = client.post(f"/games/sessions/{session_id}/answer", 
                                        json=answer_data, headers=headers)
            assert answer_response.status_code == 200
            
            result = answer_response.json()
            assert result["is_correct"] is True
            
            current_score += question.points
            assert result["current_score"] == current_score
            
            if i == len(test_quiz.questions) - 1:
                assert result["session_completed"] is True
        
        # 7. Verificar resultados finales
        results_response = client.get(f"/games/sessions/{session_id}/results", headers=headers)
        assert results_response.status_code == 200
        
        results = results_response.json()
        assert results["score"] == current_score
        assert results["correct_answers"] == len(test_quiz.questions)
        assert results["incorrect_answers"] == 0
        
        # 8. Verificar historial
        history_response = client.get("/games/history", headers=headers)
        assert history_response.status_code == 200
        
        history = history_response.json()
        assert len(history["sessions"]) >= 1
        assert history["sessions"][0]["quiz_title"] == test_quiz.title
    
    def test_complete_teacher_flow(self, client: TestClient, db_session: Session):
        """Test flujo completo: registro de profesor -> dashboard -> ver resultados"""
        
        # 1. Registro de profesor
        teacher_data = {
            "email": "integration_teacher@ludix.com",
            "password": "teacher123",
            "name": "Integration Teacher",
            "role": "teacher"
        }
        
        register_response = client.post("/auth/register", json=teacher_data)
        assert register_response.status_code == 200
        
        register_data = register_response.json()
        teacher_token = register_data["access_token"]
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        # 2. Verificar perfil del profesor
        profile_response = client.get("/users/profile", headers=headers)
        assert profile_response.status_code == 200
        
        profile_data = profile_response.json()
        assert_user_data(profile_data, teacher_data["email"], "teacher")
        
        # 3. Actualizar perfil
        update_data = {
            "name": "Updated Integration Teacher",
            "avatar_url": "https://example.com/teacher-avatar.jpg"
        }
        
        update_response = client.put("/users/profile", json=update_data, headers=headers)
        assert update_response.status_code == 200
        
        updated_profile = update_response.json()
        assert updated_profile["name"] == update_data["name"]
        assert updated_profile["avatar_url"] == update_data["avatar_url"]
        
        # 4. Verificar dashboard del profesor
        dashboard_response = client.get("/users/teacher/dashboard", headers=headers)
        assert dashboard_response.status_code == 200
        
        dashboard = dashboard_response.json()
        assert "teacher" in dashboard
        assert "classes" in dashboard
        assert "total_students" in dashboard
        assert dashboard["teacher"]["name"] == update_data["name"]


class TestAuthenticationFlow:
    """Test de flujos de autenticación completos"""
    
    def test_login_logout_flow(self, client: TestClient, test_student: User):
        """Test flujo login -> uso de API -> logout"""
        
        # 1. Login
        login_data = {
            "email": test_student.email,
            "password": "student123"
        }
        
        login_response = client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        login_result = login_response.json()
        access_token = login_result["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Usar API con token
        profile_response = client.get("/users/profile", headers=headers)
        assert profile_response.status_code == 200
        
        # 3. Logout
        logout_response = client.post("/auth/logout", headers=headers)
        assert logout_response.status_code == 200
        
        # 4. Token debería seguir funcionando (logout es simbólico en esta implementación)
        profile_response2 = client.get("/users/profile", headers=headers)
        assert profile_response2.status_code == 200
    
    def test_token_refresh_flow(self, client: TestClient, test_teacher: User):
        """Test flujo de renovación de tokens"""
        
        # 1. Login
        login_data = {
            "email": test_teacher.email,
            "password": "teacher123"
        }
        
        login_response = client.post("/auth/login", json=login_data)
        login_result = login_response.json()
        
        original_access_token = login_result["access_token"]
        refresh_token = login_result["refresh_token"]
        
        # 2. Usar refresh token para obtener nuevo access token
        refresh_data = {"refresh_token": refresh_token}
        refresh_response = client.post("/auth/refresh", json=refresh_data)
        assert refresh_response.status_code == 200
        
        refresh_result = refresh_response.json()
        new_access_token = refresh_result["access_token"]
        new_refresh_token = refresh_result["refresh_token"]
        
        # 3. Verificar que son tokens diferentes
        assert new_access_token != original_access_token
        assert new_refresh_token != refresh_token
        
        # 4. Verificar que el nuevo token funciona
        headers = {"Authorization": f"Bearer {new_access_token}"}
        profile_response = client.get("/users/profile", headers=headers)
        assert profile_response.status_code == 200


class TestErrorRecoveryFlow:
    """Test de flujos de recuperación de errores"""
    
    def test_invalid_game_session_recovery(self, client: TestClient, auth_headers_student: dict,
                                         enrolled_student: User, test_quiz: Quiz):
        """Test recuperación de errores en sesión de juego"""
        
        # 1. Iniciar sesión válida
        start_response = client.post(f"/games/{test_quiz.id}/start", headers=auth_headers_student)
        assert start_response.status_code == 200
        
        session_data = start_response.json()
        session_id = session_data["id"]
        
        # 2. Intentar responder con datos inválidos
        invalid_answer_data = {
            "question_id": "invalid-question-id",
            "selected_answer": 0,
            "time_taken_seconds": 15
        }
        
        invalid_response = client.post(f"/games/sessions/{session_id}/answer", 
                                     json=invalid_answer_data, headers=auth_headers_student)
        assert invalid_response.status_code == 400
        
        # 3. Recuperar con respuesta válida
        first_question = test_quiz.questions[0]
        valid_answer_data = {
            "question_id": str(first_question.id),
            "selected_answer": first_question.correct_answer,
            "time_taken_seconds": 15
        }
        
        valid_response = client.post(f"/games/sessions/{session_id}/answer", 
                                   json=valid_answer_data, headers=auth_headers_student)
        assert valid_response.status_code == 200
        
        result = valid_response.json()
        assert result["is_correct"] is True
    
    def test_multiple_login_attempts(self, client: TestClient, test_teacher: User):
        """Test múltiples intentos de login"""
        
        # 1. Login fallido
        invalid_login = {
            "email": test_teacher.email,
            "password": "wrong_password"
        }
        
        fail_response = client.post("/auth/login", json=invalid_login)
        assert fail_response.status_code == 401
        
        # 2. Login exitoso después del fallo
        valid_login = {
            "email": test_teacher.email,
            "password": "teacher123"
        }
        
        success_response = client.post("/auth/login", json=valid_login)
        assert success_response.status_code == 200
        
        # 3. Verificar que puede usar la API
        token = success_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        profile_response = client.get("/users/profile", headers=headers)
        assert profile_response.status_code == 200


class TestConcurrencyFlow:
    """Test de flujos concurrentes simulados"""
    
    def test_multiple_game_sessions(self, client: TestClient, db_session: Session,
                                  enrolled_student: User, test_quiz: Quiz):
        """Test manejo de múltiples sesiones de juego"""
        
        # Crear token para el estudiante
        from services.AuthService import auth_service
        token_data = {
            "sub": str(enrolled_student.id),
            "email": enrolled_student.email,
            "role": enrolled_student.role.value
        }
        token = auth_service.create_access_token(token_data)
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. Iniciar primera sesión
        start_response1 = client.post(f"/games/{test_quiz.id}/start", headers=headers)
        assert start_response1.status_code == 200
        
        session1_data = start_response1.json()
        session1_id = session1_data["id"]
        
        # 2. Intentar iniciar segunda sesión (debería devolver la misma)
        start_response2 = client.post(f"/games/{test_quiz.id}/start", headers=headers)
        assert start_response2.status_code == 200
        
        session2_data = start_response2.json()
        assert session2_data["id"] == session1_id  # Misma sesión
        
        # 3. Completar la sesión
        for question in test_quiz.questions:
            answer_data = {
                "question_id": str(question.id),
                "selected_answer": question.correct_answer,
                "time_taken_seconds": 10
            }
            
            answer_response = client.post(f"/games/sessions/{session1_id}/answer", 
                                        json=answer_data, headers=headers)
            assert answer_response.status_code == 200
        
        # 4. Ahora debería poder iniciar una nueva sesión
        start_response3 = client.post(f"/games/{test_quiz.id}/start", headers=headers)
        assert start_response3.status_code == 200
        
        session3_data = start_response3.json()
        assert session3_data["id"] != session1_id  # Nueva sesión


class TestDataConsistencyFlow:
    """Test de consistencia de datos a través de flujos"""
    
    def test_profile_update_consistency(self, client: TestClient, db_session: Session, test_student: User):
        """Test consistencia de actualizaciones de perfil"""
        
        # Crear token
        from services.AuthService import auth_service
        token_data = {
            "sub": str(test_student.id),
            "email": test_student.email,
            "role": test_student.role.value
        }
        token = auth_service.create_access_token(token_data)
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. Obtener perfil inicial
        initial_response = client.get("/users/profile", headers=headers)
        initial_data = initial_response.json()
        
        # 2. Actualizar perfil
        update_data = {
            "name": "Consistent Test Student",
            "avatar_url": "https://example.com/consistent-avatar.jpg",
            "mascot": "phoenix"
        }
        
        update_response = client.put("/users/profile", json=update_data, headers=headers)
        assert update_response.status_code == 200
        
        # 3. Verificar inmediatamente después
        immediate_response = client.get("/users/profile", headers=headers)
        immediate_data = immediate_response.json()
        
        assert immediate_data["name"] == update_data["name"]
        assert immediate_data["avatar_url"] == update_data["avatar_url"]
        assert immediate_data["mascot"] == update_data["mascot"]
        
        # 4. Verificar después de refresh de DB
        db_session.expire(test_student)
        db_session.refresh(test_student)
        
        final_response = client.get("/users/profile", headers=headers)
        final_data = final_response.json()
        
        assert final_data["name"] == update_data["name"]
        assert final_data["avatar_url"] == update_data["avatar_url"]
        assert final_data["mascot"] == update_data["mascot"]
