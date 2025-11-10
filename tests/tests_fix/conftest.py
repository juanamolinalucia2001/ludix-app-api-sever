import pytest
from httpx import AsyncClient
from main import app
from services.supabase_service import supabase_service
import asyncio
import uuid


@pytest.fixture(scope="session")
def event_loop():
    """Crea un bucle de eventos para toda la sesión de tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def client():
    """Cliente HTTP asíncrono para testear FastAPI."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def teacher_headers():
    """Headers simulados de un docente autenticado."""
    return {
        "Authorization": "Bearer fake_teacher_token",
        "role": "TEACHER",
        "id": str(uuid.uuid4())
    }


@pytest.fixture
def student_headers():
    """Headers simulados de un estudiante autenticado."""
    return {
        "Authorization": "Bearer fake_student_token",
        "role": "STUDENT",
        "id": str(uuid.uuid4()),
        "class_id": str(uuid.uuid4())
    }


@pytest.fixture
async def make_class(client):
    """Crea una clase simulada vía API."""
    async def _make_class(headers, name="Clase Test"):
        response = await client.post(
            "/classes/",
            json={"name": name, "grade": "5A"},
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"id": str(uuid.uuid4()), "name": name, "class_code": "TEST123"}
    return _make_class


@pytest.fixture
async def make_quiz(client):
    """Crea un quiz de prueba."""
    async def _make_quiz(headers, class_id, title="Quiz Test"):
        response = await client.post(
            "/quizzes/",
            json={
                "title": title,
                "description": "Quiz generado para test",
                "class_id": class_id,
                "questions": [
                    {
                        "question_text": "¿Cuánto es 2 + 2?",
                        "question_type": "multiple_choice",
                        "options": ["2", "3", "4", "5"],
                        "correct_answer": 2,
                        "points": 10
                    }
                ]
            },
            headers=headers
        )
        return response
    return _make_quiz


@pytest.fixture
async def make_student():
    """Crea un estudiante simulado."""
    async def _make_student(name="Estudiante Test", avatar="/avatars/default.png", mascot="loro"):
        student_id = str(uuid.uuid4())
        return {
            "id": student_id,
            "name": name,
            "avatar": avatar,
            "mascot": mascot,
            "headers": {
                "Authorization": f"Bearer fake_token_{student_id}",
                "role": "STUDENT",
                "id": student_id
            }
        }
    return _make_student
