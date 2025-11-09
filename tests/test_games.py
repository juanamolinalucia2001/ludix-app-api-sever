"""
Tests para los endpoints de juegos
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.User import User
from models.Quiz import Quiz, Class, Question
from models.GameSession import GameSession, SessionStatus
from tests.conftest import create_test_game_session


class TestGameEndpoints:
    """Test suite para endpoints de juegos"""
    
    def test_get_available_games_student_enrolled(self, client: TestClient, auth_headers_student: dict,
                                                 enrolled_student: User, test_quiz: Quiz):
        """Test obtener juegos disponibles como estudiante inscrito"""
        response = client.get("/games/", headers=auth_headers_student)
        
        assert response.status_code == 200
        games = response.json()
        
        assert isinstance(games, list)
        assert len(games) >= 1
        
        # Verificar estructura de juego
        game = games[0]
        assert "id" in game
        assert "title" in game
        assert "description" in game
        assert "last_played" in game
        assert "best_score" in game
        assert "can_play" in game
        assert game["can_play"] is True
    
    def test_get_available_games_student_not_enrolled(self, client: TestClient, auth_headers_student: dict):
        """Test obtener juegos como estudiante no inscrito en clase"""
        response = client.get("/games/", headers=auth_headers_student)
        
        assert response.status_code == 400
        assert "Student must be enrolled in a class" in response.json()["detail"]
    
    def test_get_available_games_as_teacher_forbidden(self, client: TestClient, auth_headers_teacher: dict):
        """Test que profesor no puede obtener lista de juegos (endpoint para estudiantes)"""
        response = client.get("/games/", headers=auth_headers_teacher)
        
        assert response.status_code == 401  # Unauthorized debido a get_current_student
    
    def test_get_available_games_unauthorized(self, client: TestClient):
        """Test obtener juegos sin autenticación"""
        response = client.get("/games/")
        
        assert response.status_code == 403
    
    def test_start_game_session_success(self, client: TestClient, auth_headers_student: dict,
                                      enrolled_student: User, test_quiz: Quiz):
        """Test iniciar sesión de juego exitosamente"""
        response = client.post(f"/games/{test_quiz.id}/start", headers=auth_headers_student)
        
        assert response.status_code == 200
        session_data = response.json()
        
        # Verificar estructura de respuesta
        assert "id" in session_data
        assert "quiz_id" in session_data
        assert "status" in session_data
        assert "current_question" in session_data
        assert "score" in session_data
        assert "total_questions" in session_data
        assert "start_time" in session_data
        assert "quiz_title" in session_data
        
        # Verificar valores iniciales
        assert session_data["quiz_id"] == str(test_quiz.id)
        assert session_data["status"] == "in_progress"
        assert session_data["current_question"] == 0
        assert session_data["score"] == 0
        assert session_data["total_questions"] == len(test_quiz.questions)
        assert session_data["quiz_title"] == test_quiz.title
    
    def test_start_game_session_resume_existing(self, client: TestClient, auth_headers_student: dict,
                                              db_session: Session, enrolled_student: User, test_quiz: Quiz):
        """Test reanudar sesión de juego existente"""
        # Crear sesión existente
        existing_session = create_test_game_session(db_session, enrolled_student, test_quiz)
        existing_session.current_question = 1
        existing_session.score = 10
        db_session.commit()
        
        response = client.post(f"/games/{test_quiz.id}/start", headers=auth_headers_student)
        
        assert response.status_code == 200
        session_data = response.json()
        
        # Debería devolver la sesión existente
        assert session_data["id"] == str(existing_session.id)
        assert session_data["current_question"] == 1
        assert session_data["score"] == 10
    
    def test_start_game_session_quiz_not_found(self, client: TestClient, auth_headers_student: dict,
                                             enrolled_student: User):
        """Test iniciar juego con quiz inexistente"""
        fake_quiz_id = "fake-quiz-id"
        response = client.post(f"/games/{fake_quiz_id}/start", headers=auth_headers_student)
        
        assert response.status_code == 404
        assert "Quiz not found or not accessible" in response.json()["detail"]
    
    def test_start_game_session_student_not_enrolled(self, client: TestClient, auth_headers_student: dict,
                                                   test_quiz: Quiz):
        """Test iniciar juego como estudiante no inscrito"""
        response = client.post(f"/games/{test_quiz.id}/start", headers=auth_headers_student)
        
        assert response.status_code == 404  # El quiz no será accesible para el estudiante
    
    def test_submit_answer_correct(self, client: TestClient, auth_headers_student: dict,
                                 db_session: Session, enrolled_student: User, test_quiz: Quiz):
        """Test enviar respuesta correcta"""
        # Crear sesión de juego
        session = create_test_game_session(db_session, enrolled_student, test_quiz)
        
        # Obtener la primera pregunta
        first_question = test_quiz.questions[0]
        
        answer_data = {
            "question_id": str(first_question.id),
            "selected_answer": first_question.correct_answer,
            "time_taken_seconds": 15,
            "hint_used": False,
            "confidence_level": 5
        }
        
        response = client.post(f"/games/sessions/{session.id}/answer", 
                             json=answer_data, headers=auth_headers_student)
        
        assert response.status_code == 200
        result = response.json()
        
        # Verificar respuesta
        assert result["session_id"] == str(session.id)
        assert result["question_answered"] == str(first_question.id)
        assert result["is_correct"] is True
        assert result["current_score"] == first_question.points
        assert result["current_question"] == 1
        assert result["session_completed"] is False
        
        # Debería incluir la siguiente pregunta
        assert "next_question" in result
    
    def test_submit_answer_incorrect(self, client: TestClient, auth_headers_student: dict,
                                   db_session: Session, enrolled_student: User, test_quiz: Quiz):
        """Test enviar respuesta incorrecta"""
        # Crear sesión de juego
        session = create_test_game_session(db_session, enrolled_student, test_quiz)
        
        # Obtener la primera pregunta
        first_question = test_quiz.questions[0]
        wrong_answer = (first_question.correct_answer + 1) % len(first_question.options)
        
        answer_data = {
            "question_id": str(first_question.id),
            "selected_answer": wrong_answer,
            "time_taken_seconds": 30,
            "hint_used": True
        }
        
        response = client.post(f"/games/sessions/{session.id}/answer", 
                             json=answer_data, headers=auth_headers_student)
        
        assert response.status_code == 200
        result = response.json()
        
        # Verificar respuesta
        assert result["is_correct"] is False
        assert result["current_score"] == 0  # No puntos por respuesta incorrecta
    
    def test_submit_answer_complete_quiz(self, client: TestClient, auth_headers_student: dict,
                                       db_session: Session, enrolled_student: User, test_quiz: Quiz):
        """Test completar quiz enviando todas las respuestas"""
        # Crear sesión de juego
        session = create_test_game_session(db_session, enrolled_student, test_quiz)
        
        total_score = 0
        
        # Responder todas las preguntas
        for i, question in enumerate(test_quiz.questions):
            answer_data = {
                "question_id": str(question.id),
                "selected_answer": question.correct_answer,
                "time_taken_seconds": 20,
                "hint_used": False
            }
            
            response = client.post(f"/games/sessions/{session.id}/answer", 
                                 json=answer_data, headers=auth_headers_student)
            
            assert response.status_code == 200
            result = response.json()
            
            total_score += question.points
            assert result["current_score"] == total_score
            
            # La última pregunta debería completar la sesión
            if i == len(test_quiz.questions) - 1:
                assert result["session_completed"] is True
                assert "final_score" in result
                assert "correct_answers" in result
                assert "incorrect_answers" in result
                assert "percentage_score" in result
                assert result["final_score"] == total_score
            else:
                assert result["session_completed"] is False
                assert "next_question" in result
    
    def test_submit_answer_invalid_session(self, client: TestClient, auth_headers_student: dict):
        """Test enviar respuesta con sesión inválida"""
        fake_session_id = "fake-session-id"
        answer_data = {
            "question_id": "fake-question-id",
            "selected_answer": 0,
            "time_taken_seconds": 15
        }
        
        response = client.post(f"/games/sessions/{fake_session_id}/answer", 
                             json=answer_data, headers=auth_headers_student)
        
        assert response.status_code == 404
        assert "Game session not found or not active" in response.json()["detail"]
    
    def test_submit_answer_wrong_question_id(self, client: TestClient, auth_headers_student: dict,
                                           db_session: Session, enrolled_student: User, test_quiz: Quiz):
        """Test enviar respuesta con ID de pregunta incorrecto"""
        # Crear sesión de juego
        session = create_test_game_session(db_session, enrolled_student, test_quiz)
        
        answer_data = {
            "question_id": "wrong-question-id",
            "selected_answer": 0,
            "time_taken_seconds": 15
        }
        
        response = client.post(f"/games/sessions/{session.id}/answer", 
                             json=answer_data, headers=auth_headers_student)
        
        assert response.status_code == 400
        assert "Question ID does not match current question" in response.json()["detail"]
    
    def test_get_session_results_student(self, client: TestClient, auth_headers_student: dict,
                                       db_session: Session, enrolled_student: User, test_quiz: Quiz):
        """Test obtener resultados de sesión como estudiante"""
        # Crear sesión completada
        session = create_test_game_session(db_session, enrolled_student, test_quiz)
        session.status = SessionStatus.COMPLETED
        session.score = 20
        session.correct_answers = 2
        session.incorrect_answers = 0
        db_session.commit()
        
        response = client.get(f"/games/sessions/{session.id}/results", headers=auth_headers_student)
        
        assert response.status_code == 200
        results = response.json()
        
        # Verificar estructura de resultados
        assert "id" in results
        assert "score" in results
        assert "correct_answers" in results
        assert "incorrect_answers" in results
        assert "quiz" in results
        assert results["score"] == 20
        assert results["correct_answers"] == 2
    
    def test_get_session_results_teacher(self, client: TestClient, auth_headers_teacher: dict,
                                       db_session: Session, test_teacher: User, enrolled_student: User, test_quiz: Quiz):
        """Test obtener resultados de sesión como profesor (creador del quiz)"""
        # Crear sesión completada
        session = create_test_game_session(db_session, enrolled_student, test_quiz)
        session.status = SessionStatus.COMPLETED
        db_session.commit()
        
        response = client.get(f"/games/sessions/{session.id}/results", headers=auth_headers_teacher)
        
        assert response.status_code == 200
        results = response.json()
        
        # Como profesor, debería incluir información del estudiante
        assert "student" in results
        assert results["student"]["id"] == str(enrolled_student.id)
        assert results["student"]["name"] == enrolled_student.name
    
    def test_get_session_results_access_denied(self, client: TestClient, auth_headers_student: dict,
                                             db_session: Session, test_teacher: User, test_quiz: Quiz):
        """Test acceso denegado a resultados de sesión de otro estudiante"""
        # Crear otro estudiante y su sesión
        from models.User import User, UserRole
        other_student = User(
            email="other@ludix.com",
            name="Other Student",
            hashed_password="hash",
            role=UserRole.STUDENT,
            class_id=test_quiz.class_id
        )
        db_session.add(other_student)
        db_session.commit()
        
        session = create_test_game_session(db_session, other_student, test_quiz)
        
        response = client.get(f"/games/sessions/{session.id}/results", headers=auth_headers_student)
        
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]
    
    def test_get_game_history(self, client: TestClient, auth_headers_student: dict,
                            db_session: Session, enrolled_student: User, test_quiz: Quiz):
        """Test obtener historial de juegos del estudiante"""
        # Crear algunas sesiones
        session1 = create_test_game_session(db_session, enrolled_student, test_quiz)
        session1.status = SessionStatus.COMPLETED
        session1.score = 15
        
        session2 = create_test_game_session(db_session, enrolled_student, test_quiz)
        session2.status = SessionStatus.COMPLETED
        session2.score = 20
        
        db_session.commit()
        
        response = client.get("/games/history", headers=auth_headers_student)
        
        assert response.status_code == 200
        history = response.json()
        
        # Verificar estructura de respuesta
        assert "sessions" in history
        assert "total" in history
        assert "limit" in history
        assert "offset" in history
        
        sessions = history["sessions"]
        assert len(sessions) >= 2
        
        # Verificar que incluye título del quiz
        for session in sessions:
            assert "quiz_title" in session
            assert session["quiz_title"] == test_quiz.title
    
    def test_get_game_history_pagination(self, client: TestClient, auth_headers_student: dict):
        """Test paginación del historial de juegos"""
        response = client.get("/games/history?limit=5&offset=0", headers=auth_headers_student)
        
        assert response.status_code == 200
        history = response.json()
        
        assert history["limit"] == 5
        assert history["offset"] == 0
    
    def test_get_game_history_as_teacher_forbidden(self, client: TestClient, auth_headers_teacher: dict):
        """Test que profesor no puede obtener historial (endpoint para estudiantes)"""
        response = client.get("/games/history", headers=auth_headers_teacher)
        
        assert response.status_code == 401  # Unauthorized debido a get_current_student
    
    @pytest.mark.parametrize("missing_field", ["question_id", "selected_answer", "time_taken_seconds"])
    def test_submit_answer_missing_fields(self, client: TestClient, auth_headers_student: dict,
                                        db_session: Session, enrolled_student: User, test_quiz: Quiz, missing_field: str):
        """Test enviar respuesta con campos faltantes"""
        session = create_test_game_session(db_session, enrolled_student, test_quiz)
        first_question = test_quiz.questions[0]
        
        answer_data = {
            "question_id": str(first_question.id),
            "selected_answer": 0,
            "time_taken_seconds": 15
        }
        
        # Remover el campo especificado
        del answer_data[missing_field]
        
        response = client.post(f"/games/sessions/{session.id}/answer", 
                             json=answer_data, headers=auth_headers_student)
        
        assert response.status_code == 422  # Validation error
