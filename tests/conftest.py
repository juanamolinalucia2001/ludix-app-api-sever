"""
Configuración de pytest para los tests de Ludix API con Supabase
Versión simplificada usando solo Supabase (sin SQLAlchemy)
"""

import pytest
import asyncio
import os
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid

# Imports del proyecto
from main import app
from core.config import settings

# Test settings
TEST_SUPABASE_URL = os.getenv("TEST_SUPABASE_URL", "https://test.supabase.co")
TEST_SUPABASE_KEY = os.getenv("TEST_SUPABASE_KEY", "test-key")
TEST_SUPABASE_SERVICE_KEY = os.getenv("TEST_SUPABASE_SERVICE_KEY", "test-service-key")

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def mock_supabase_service():
    """Mock del servicio de Supabase para tests"""
    with patch('services.supabase_service.supabase_service') as mock_service:
        # Mock methods
        mock_service.create_user = MagicMock()
        mock_service.get_user_by_email = MagicMock()
        mock_service.get_user_by_id = MagicMock()
        mock_service.authenticate_user = MagicMock()
        mock_service.update_user = MagicMock()
        mock_service.create_class = MagicMock()
        mock_service.get_teacher_classes = MagicMock()
        mock_service.create_quiz = MagicMock()
        mock_service.get_class_quizzes = MagicMock()
        mock_service.create_game_session = MagicMock()
        mock_service.update_game_session = MagicMock()
        mock_service.get_student_sessions = MagicMock()
        mock_service.enroll_student = MagicMock()
        mock_service.get_class_students = MagicMock()
        
        yield mock_service

@pytest.fixture(scope="function")
def client(mock_supabase_service) -> Generator[TestClient, None, None]:
    """Create a test client with mocked Supabase"""
    
    # Override Supabase settings for testing
    with patch.object(settings, 'SUPABASE_URL', TEST_SUPABASE_URL), \
         patch.object(settings, 'SUPABASE_KEY', TEST_SUPABASE_KEY), \
         patch.object(settings, 'SUPABASE_SERVICE_KEY', TEST_SUPABASE_SERVICE_KEY):
        
        with TestClient(app) as test_client:
            yield test_client

@pytest.fixture
def test_teacher_data() -> Dict[str, Any]:
    """Datos de prueba para profesor"""
    return {
        "id": str(uuid.uuid4()),
        "email": "teacher@ludix.com",
        "full_name": "Test Teacher",
        "role": "teacher",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }

@pytest.fixture
def test_student_data() -> Dict[str, Any]:
    """Datos de prueba para estudiante"""
    return {
        "id": str(uuid.uuid4()),
        "email": "student@ludix.com",
        "full_name": "Test Student",
        "role": "student",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }

@pytest.fixture
def test_class_data(test_teacher_data) -> Dict[str, Any]:
    """Datos de prueba para clase"""
    return {
        "id": str(uuid.uuid4()),
        "name": "Test Class",
        "description": "A test class for testing",
        "teacher_id": test_teacher_data["id"],
        "code": "TEST001",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }

@pytest.fixture
def test_quiz_data(test_teacher_data, test_class_data) -> Dict[str, Any]:
    """Datos de prueba para quiz"""
    return {
        "id": str(uuid.uuid4()),
        "title": "Test Quiz",
        "description": "A test quiz for testing",
        "questions": [
            {
                "id": str(uuid.uuid4()),
                "question_text": "What is 2 + 2?",
                "options": ["3", "4", "5", "6"],
                "correct_answer": 1,
                "points": 10
            },
            {
                "id": str(uuid.uuid4()),
                "question_text": "What is the capital of France?",
                "options": ["London", "Berlin", "Paris", "Madrid"],
                "correct_answer": 2,
                "points": 10
            }
        ],
        "class_id": test_class_data["id"],
        "created_by": test_teacher_data["id"],
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }

@pytest.fixture
def teacher_token(test_teacher_data) -> str:
    """Generate a JWT token for the test teacher"""
    from routers.auth_supabase import create_access_token
    
    token_data = {
        "sub": test_teacher_data["id"],
        "email": test_teacher_data["email"],
        "role": test_teacher_data["role"]
    }
    return create_access_token(token_data)

@pytest.fixture
def student_token(test_student_data) -> str:
    """Generate a JWT token for the test student"""
    from routers.auth_supabase import create_access_token
    
    token_data = {
        "sub": test_student_data["id"],
        "email": test_student_data["email"],
        "role": test_student_data["role"]
    }
    return create_access_token(token_data)

@pytest.fixture
def auth_headers_teacher(teacher_token: str) -> Dict[str, str]:
    """Create authorization headers for teacher"""
    return {"Authorization": f"Bearer {teacher_token}"}

@pytest.fixture
def auth_headers_student(student_token: str) -> Dict[str, str]:
    """Create authorization headers for student"""
    return {"Authorization": f"Bearer {student_token}"}

@pytest.fixture
def enrolled_student_data(test_student_data, test_class_data) -> Dict[str, Any]:
    """Create a student enrolled in a class"""
    student_data = test_student_data.copy()
    student_data["class_id"] = test_class_data["id"]
    return student_data

# Utility functions for tests
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

def create_test_game_session_data(student_data: Dict[str, Any], quiz_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create test game session data"""
    return {
        "id": str(uuid.uuid4()),
        "student_id": student_data["id"],
        "quiz_id": quiz_data["id"],
        "answers": [],
        "score": 0,
        "max_score": sum(q["points"] for q in quiz_data["questions"]),
        "created_at": "2024-01-01T00:00:00Z"
    }
