"""
Tests para los endpoints de autenticación
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.User import User, UserRole
from tests.conftest import assert_valid_token_response, assert_user_data


class TestAuthEndpoints:
    """Test suite para endpoints de autenticación"""
    
    def test_register_teacher_success(self, client: TestClient, db_session: Session):
        """Test registro exitoso de profesor"""
        user_data = {
            "email": "newteacher@ludix.com",
            "password": "password123",
            "name": "New Teacher",
            "role": "teacher"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Verificar estructura de respuesta
        assert_valid_token_response(response_data)
        assert_user_data(response_data["user"], user_data["email"], "teacher")
        
        # Verificar que el usuario fue creado en la base de datos
        user = db_session.query(User).filter(User.email == user_data["email"]).first()
        assert user is not None
        assert user.name == user_data["name"]
        assert user.role == UserRole.TEACHER
        assert user.is_active is True
    
    def test_register_student_success(self, client: TestClient, db_session: Session):
        """Test registro exitoso de estudiante"""
        user_data = {
            "email": "newstudent@ludix.com",
            "password": "password123",
            "name": "New Student",
            "role": "student"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Verificar estructura de respuesta
        assert_valid_token_response(response_data)
        assert_user_data(response_data["user"], user_data["email"], "student")
        
        # Verificar que el usuario fue creado en la base de datos
        user = db_session.query(User).filter(User.email == user_data["email"]).first()
        assert user is not None
        assert user.name == user_data["name"]
        assert user.role == UserRole.STUDENT
    
    def test_register_duplicate_email(self, client: TestClient, test_teacher: User):
        """Test registro con email duplicado"""
        user_data = {
            "email": test_teacher.email,
            "password": "password123",
            "name": "Another User",
            "role": "teacher"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_register_invalid_role(self, client: TestClient):
        """Test registro con rol inválido"""
        user_data = {
            "email": "invalid@ludix.com",
            "password": "password123",
            "name": "Invalid Role User",
            "role": "admin"  # Rol no válido
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "Role must be 'teacher' or 'student'" in response.json()["detail"]
    
    def test_register_invalid_email(self, client: TestClient):
        """Test registro con email inválido"""
        user_data = {
            "email": "invalid-email",  # Email malformado
            "password": "password123",
            "name": "Test User",
            "role": "teacher"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_login_teacher_success(self, client: TestClient, test_teacher: User):
        """Test login exitoso de profesor"""
        login_data = {
            "email": test_teacher.email,
            "password": "teacher123"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Verificar estructura de respuesta
        assert_valid_token_response(response_data)
        assert_user_data(response_data["user"], test_teacher.email, "teacher")
    
    def test_login_student_success(self, client: TestClient, test_student: User):
        """Test login exitoso de estudiante"""
        login_data = {
            "email": test_student.email,
            "password": "student123"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Verificar estructura de respuesta
        assert_valid_token_response(response_data)
        assert_user_data(response_data["user"], test_student.email, "student")
    
    def test_login_invalid_credentials(self, client: TestClient, test_teacher: User):
        """Test login con credenciales incorrectas"""
        login_data = {
            "email": test_teacher.email,
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login con usuario que no existe"""
        login_data = {
            "email": "nonexistent@ludix.com",
            "password": "password123"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_inactive_user(self, client: TestClient, db_session: Session):
        """Test login con usuario inactivo"""
        # Crear usuario inactivo
        inactive_user = User(
            email="inactive@ludix.com",
            name="Inactive User",
            hashed_password="hashed_password",
            role=UserRole.STUDENT,
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        login_data = {
            "email": inactive_user.email,
            "password": "password123"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 403
        assert "User account is disabled" in response.json()["detail"]
    
    def test_get_current_user_info(self, client: TestClient, auth_headers_teacher: dict, test_teacher: User):
        """Test obtener información del usuario actual"""
        response = client.get("/auth/me", headers=auth_headers_teacher)
        
        assert response.status_code == 200
        user_data = response.json()
        
        assert_user_data(user_data, test_teacher.email, "teacher")
        assert user_data["id"] == str(test_teacher.id)
        assert user_data["name"] == test_teacher.name
    
    def test_get_current_user_info_invalid_token(self, client: TestClient):
        """Test obtener información con token inválido"""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
        assert "Invalid authentication token" in response.json()["detail"]
    
    def test_get_current_user_info_no_token(self, client: TestClient):
        """Test obtener información sin token"""
        response = client.get("/auth/me")
        
        assert response.status_code == 403  # FastAPI returns 403 for missing token
    
    def test_refresh_token_success(self, client: TestClient, test_teacher: User):
        """Test renovación exitosa de token"""
        # Primero hacer login para obtener refresh token
        login_data = {
            "email": test_teacher.email,
            "password": "teacher123"
        }
        
        login_response = client.post("/auth/login", json=login_data)
        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]
        
        # Usar refresh token para obtener nuevo access token
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Verificar estructura de respuesta
        assert_valid_token_response(response_data)
        assert_user_data(response_data["user"], test_teacher.email, "teacher")
        
        # Verificar que es un token diferente
        assert response_data["access_token"] != login_data["access_token"]
    
    def test_refresh_token_invalid(self, client: TestClient):
        """Test renovación con refresh token inválido"""
        refresh_data = {"refresh_token": "invalid_refresh_token"}
        
        response = client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]
    
    def test_logout_success(self, client: TestClient, auth_headers_teacher: dict):
        """Test logout exitoso"""
        response = client.post("/auth/logout", headers=auth_headers_teacher)
        
        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]
    
    def test_logout_invalid_token(self, client: TestClient):
        """Test logout con token inválido"""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.post("/auth/logout", headers=headers)
        
        # Debería funcionar igualmente (logout es idempotente)
        assert response.status_code == 200
    
    def test_google_auth_not_implemented(self, client: TestClient):
        """Test que Google Auth retorna not implemented"""
        google_data = {
            "google_token": "fake_google_token",
            "role": "student"
        }
        
        response = client.post("/auth/google", json=google_data)
        
        assert response.status_code == 501
        assert "Google authentication will be implemented" in response.json()["detail"]
    
    @pytest.mark.parametrize("missing_field", ["email", "password", "name", "role"])
    def test_register_missing_fields(self, client: TestClient, missing_field: str):
        """Test registro con campos faltantes"""
        user_data = {
            "email": "test@ludix.com",
            "password": "password123",
            "name": "Test User",
            "role": "teacher"
        }
        
        # Remover el campo especificado
        del user_data[missing_field]
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.parametrize("missing_field", ["email", "password"])
    def test_login_missing_fields(self, client: TestClient, missing_field: str):
        """Test login con campos faltantes"""
        login_data = {
            "email": "test@ludix.com",
            "password": "password123"
        }
        
        # Remover el campo especificado
        del login_data[missing_field]
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 422  # Validation error
