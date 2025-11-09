"""
Tests para los endpoints de autenticación con Supabase
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
import uuid
from typing import Dict, Any

# Utility functions
def assert_valid_token_response(response_data: Dict[str, Any]):
    """Assert that response contains valid token structure"""
    assert "access_token" in response_data
    assert "refresh_token" in response_data
    assert "token_type" in response_data
    assert "expires_in" in response_data
    assert "user" in response_data
    assert response_data["token_type"] == "bearer"

def assert_user_data(user_data: Dict[str, Any], expected_email: str = None, expected_role: str = None):
    """Assert that user data contains expected fields"""
    required_fields = ["id", "email", "role"]
    for field in required_fields:
        assert field in user_data
    
    if expected_email:
        assert user_data["email"] == expected_email
    
    if expected_role:
        assert user_data["role"] == expected_role


class TestAuthSupabaseEndpoints:
    """Test suite para endpoints de autenticación con Supabase"""
    
    def test_register_teacher_success(self, client: TestClient, mock_supabase_service, test_teacher_data):
        """Test registro exitoso de profesor"""
        # Mock the service responses
        mock_supabase_service.get_user_by_email.return_value = AsyncMock(return_value=None)
        mock_supabase_service.create_user.return_value = AsyncMock(return_value=test_teacher_data)
        
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
    
    def test_register_student_success(self, client: TestClient, mock_supabase_service, test_student_data):
        """Test registro exitoso de estudiante"""
        # Mock the service responses
        mock_supabase_service.get_user_by_email.return_value = AsyncMock(return_value=None)
        mock_supabase_service.create_user.return_value = AsyncMock(return_value=test_student_data)
        
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
    
    def test_register_duplicate_email(self, client: TestClient, mock_supabase_service, test_teacher_data):
        """Test registro con email duplicado"""
        # Mock existing user
        mock_supabase_service.get_user_by_email.return_value = AsyncMock(return_value=test_teacher_data)
        
        user_data = {
            "email": test_teacher_data["email"],
            "password": "password123",
            "name": "Another User",
            "role": "teacher"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_register_invalid_role(self, client: TestClient, mock_supabase_service):
        """Test registro con rol inválido"""
        mock_supabase_service.get_user_by_email.return_value = AsyncMock(return_value=None)
        
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
    
    def test_login_success(self, client: TestClient, mock_supabase_service, test_teacher_data):
        """Test login exitoso"""
        # Mock authentication
        auth_result = {
            "id": test_teacher_data["id"],
            "email": test_teacher_data["email"],
            "name": test_teacher_data["full_name"],
            "role": test_teacher_data["role"],
            "is_active": True
        }
        
        mock_supabase_service.authenticate_user.return_value = AsyncMock(return_value=auth_result)
        
        login_data = {
            "email": test_teacher_data["email"],
            "password": "teacher123"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Verificar estructura de respuesta
        assert_valid_token_response(response_data)
        assert_user_data(response_data["user"], test_teacher_data["email"], "teacher")
    
    def test_login_invalid_credentials(self, client: TestClient, mock_supabase_service):
        """Test login con credenciales incorrectas"""
        # Mock failed authentication
        mock_supabase_service.authenticate_user.return_value = AsyncMock(return_value=None)
        
        login_data = {
            "email": "test@ludix.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_get_current_user_info(self, client: TestClient, mock_supabase_service, 
                                  auth_headers_teacher: dict, test_teacher_data):
        """Test obtener información del usuario actual"""
        # Mock user lookup
        mock_supabase_service.get_user_by_id.return_value = AsyncMock(return_value=test_teacher_data)
        
        response = client.get("/auth/me", headers=auth_headers_teacher)
        
        assert response.status_code == 200
        user_data = response.json()
        
        assert user_data["id"] == test_teacher_data["id"]
        assert user_data["email"] == test_teacher_data["email"]
    
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
    
    def test_logout_success(self, client: TestClient, auth_headers_teacher: dict):
        """Test logout exitoso"""
        response = client.post("/auth/logout", headers=auth_headers_teacher)
        
        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]
    
    def test_google_auth_not_implemented(self, client: TestClient):
        """Test que Google Auth retorna not implemented"""
        response = client.post("/auth/google")
        
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
    
    def test_refresh_token_success(self, client: TestClient, mock_supabase_service, test_teacher_data):
        """Test renovación exitosa de token"""
        # Mock user lookup for refresh
        mock_supabase_service.get_user_by_id.return_value = AsyncMock(return_value=test_teacher_data)
        
        # Crear un refresh token válido
        from routers.auth_supabase import create_refresh_token
        token_data = {
            "sub": test_teacher_data["id"],
            "email": test_teacher_data["email"],
            "role": test_teacher_data["role"]
        }
        refresh_token = create_refresh_token(token_data)
        
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Verificar estructura de respuesta
        assert_valid_token_response(response_data)
    
    def test_refresh_token_invalid(self, client: TestClient):
        """Test renovación con refresh token inválido"""
        refresh_data = {"refresh_token": "invalid_refresh_token"}
        
        response = client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]
