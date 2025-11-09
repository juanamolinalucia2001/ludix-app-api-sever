"""
Configuración de pytest para los tests de Ludix API con Supabase
"""

import pytest
import asyncio
import os
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Imports del proyecto (nueva arquitectura Supabase)
from main import app
from services.supabase_service import supabase_service
from core.config import settings

# Test database URL (usando SQLite para tests)
TEST_DATABASE_URL = "sqlite:///./test_ludix.db"

# Test Supabase settings
TEST_SUPABASE_URL = os.getenv("TEST_SUPABASE_URL", "https://test.supabase.co")
TEST_SUPABASE_KEY = os.getenv("TEST_SUPABASE_KEY", "test-key")
TEST_SUPABASE_SERVICE_KEY = os.getenv("TEST_SUPABASE_SERVICE_KEY", "test-service-key")

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}  # For SQLite
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a test database session"""
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database override"""
    
    # Override database dependency
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Override Supabase settings for testing
    with patch.object(settings, 'SUPABASE_URL', TEST_SUPABASE_URL), \
         patch.object(settings, 'SUPABASE_KEY', TEST_SUPABASE_KEY), \
         patch.object(settings, 'SUPABASE_SERVICE_KEY', TEST_SUPABASE_SERVICE_KEY):
        
        with TestClient(app) as test_client:
            yield test_client
    
    # Clean up overrides
    app.dependency_overrides.clear()

@pytest.fixture
def test_teacher(db_session: Session) -> User:
    """Create a test teacher user"""
    teacher = User(
        email="teacher@ludix.com",
        name="Test Teacher",
        hashed_password=auth_service.hash_password("teacher123"),
        role=UserRole.TEACHER,
        is_active=True
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)
    return teacher

@pytest.fixture
def test_student(db_session: Session) -> User:
    """Create a test student user"""
    student = User(
        email="student@ludix.com",
        name="Test Student",
        hashed_password=auth_service.hash_password("student123"),
        role=UserRole.STUDENT,
        is_active=True
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student

@pytest.fixture
def test_class(db_session: Session, test_teacher: User) -> Class:
    """Create a test class"""
    test_class = Class(
        name="Test Class",
        description="A test class for testing",
        teacher_id=test_teacher.id,
        class_code="TEST001"
    )
    db_session.add(test_class)
    db_session.commit()
    db_session.refresh(test_class)
    return test_class

@pytest.fixture
def test_quiz(db_session: Session, test_teacher: User, test_class: Class) -> Quiz:
    """Create a test quiz with questions"""
    quiz = Quiz(
        title="Test Quiz",
        description="A test quiz for testing",
        creator_id=test_teacher.id,
        class_id=test_class.id,
        is_published=True,
        is_active=True,
        order_index=1
    )
    db_session.add(quiz)
    db_session.commit()
    db_session.refresh(quiz)
    
    # Add questions
    questions = [
        Question(
            quiz_id=quiz.id,
            question_text="What is 2 + 2?",
            options=["3", "4", "5", "6"],
            correct_answer=1,  # "4"
            points=10,
            order_index=1
        ),
        Question(
            quiz_id=quiz.id,
            question_text="What is the capital of France?",
            options=["London", "Berlin", "Paris", "Madrid"],
            correct_answer=2,  # "Paris"
            points=10,
            order_index=2
        )
    ]
    
    for question in questions:
        db_session.add(question)
    
    db_session.commit()
    
    # Refresh quiz to include questions
    db_session.refresh(quiz)
    return quiz

@pytest.fixture
def teacher_token(test_teacher: User) -> str:
    """Generate a JWT token for the test teacher"""
    token_data = {
        "sub": str(test_teacher.id),
        "email": test_teacher.email,
        "role": test_teacher.role.value
    }
    return auth_service.create_access_token(token_data)

@pytest.fixture
def student_token(test_student: User) -> str:
    """Generate a JWT token for the test student"""
    token_data = {
        "sub": str(test_student.id),
        "email": test_student.email,
        "role": test_student.role.value
    }
    return auth_service.create_access_token(token_data)

@pytest.fixture
def auth_headers_teacher(teacher_token: str) -> dict:
    """Create authorization headers for teacher"""
    return {"Authorization": f"Bearer {teacher_token}"}

@pytest.fixture
def auth_headers_student(student_token: str) -> dict:
    """Create authorization headers for student"""
    return {"Authorization": f"Bearer {student_token}"}

@pytest.fixture
def enrolled_student(db_session: Session, test_student: User, test_class: Class) -> User:
    """Create a student enrolled in a class"""
    test_student.class_id = test_class.id
    db_session.commit()
    db_session.refresh(test_student)
    return test_student

# Utility functions for tests
def assert_valid_token_response(response_data: dict):
    """Assert that response contains valid token structure"""
    assert "access_token" in response_data
    assert "refresh_token" in response_data
    assert "token_type" in response_data
    assert "expires_in" in response_data
    assert "user" in response_data
    assert response_data["token_type"] == "bearer"

def assert_user_data(user_data: dict, expected_email: str = None, expected_role: str = None):
    """Assert that user data contains expected fields"""
    required_fields = ["id", "email", "name", "role", "is_active"]
    for field in required_fields:
        assert field in user_data
    
    if expected_email:
        assert user_data["email"] == expected_email
    
    if expected_role:
        assert user_data["role"] == expected_role

def create_test_game_session(db_session: Session, student: User, quiz: Quiz) -> GameSession:
    """Create a test game session"""
    from models.GameSession import SessionStatus
    
    session = GameSession(
        student_id=student.id,
        quiz_id=quiz.id,
        total_questions=len(quiz.questions),
        status=SessionStatus.IN_PROGRESS
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session
