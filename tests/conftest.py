import os
import uuid
import pytest
import pytest_asyncio  # IMPORTANTE: Necesitas importar esto
import httpx
from main import app


# Usar @pytest_asyncio.fixture para fixtures asíncronas
@pytest_asyncio.fixture
async def client():
    # Se recomienda usar una base_url válida si es posible, aunque http://test suele funcionar con httpx + app ASGI
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def uniq_email():
    def _make(prefix: str, domain="ludix.edu"):
        return f"{prefix}_{uuid.uuid4().hex[:8]}@{domain}"
    return _make


# Esta fixture necesita ser asíncrona porque usa 'await client.post'
@pytest_asyncio.fixture
async def teacher_headers(client, uniq_email):
    """Registra un docente y devuelve headers con Bearer."""
    payload = {
        "email": uniq_email("teacher"),
        "password": "DocenteSeguro2024!",
        "name": "Prof. Test",
        "role": "teacher",
    }
    # Al ser una @pytest_asyncio.fixture, pytest esperará (await) esto automáticamente
    r = await client.post("/auth/register", json=payload)
    assert r.status_code == 200, r.text
    tok = r.json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


# Las factories pueden seguir siendo síncronas y devolver funciones asíncronas
@pytest.fixture
def make_student(client, uniq_email):
    async def _factory(name="Estudiante", avatar="/avatars/a1.png", mascot="gato"):
        payload = {
            "email": uniq_email("student", "estudiante.com"),
            "password": "Estudiante123!",
            "name": name,
            "role": "student",
        }
        r = await client.post("/auth/register", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # setup perfil
        prof = await client.post("/users/setup-profile", json={
            "name": name, "avatar_url": avatar, "mascot": mascot
        }, headers=headers)
        assert prof.status_code == 200, prof.text

        return {"user": data["user"], "headers": headers}
    return _factory


@pytest.fixture
def make_class(client):
    async def _factory(headers, name="Aula de Prueba", description="Aula demo", max_students=30):
        r = await client.post("/classes/", json={
            "name": name, "description": description, "max_students": max_students
        }, headers=headers)
        assert r.status_code == 200, r.text
        return r.json()
    return _factory


@pytest.fixture
def make_quiz(client):
    async def _factory(headers, class_id, title="Quiz Demo", description="desc", difficulty="MEDIUM"):
        r = await client.post("/quizzes/", json={
            "title": title,
            "description": description,
            "class_id": class_id,
            "difficulty": difficulty,
            "questions": [
                {
                    "question_text": "¿Cuánto es 15 + 27?",
                    "question_type": "multiple_choice",
                    "options": ["40", "42", "44", "46"],
                    "correct_answer": 1,
                    "explanation": "15 + 27 = 42",
                    "difficulty": "EASY",
                    "points": 10,
                    "time_limit": 30
                },
                {
                    "question_text": "¿Cuánto es 8 × 7?",
                    "question_type": "multiple_choice",
                    "options": ["54", "56", "58", "60"],
                    "correct_answer": 1,
                    "explanation": "8 × 7 = 56",
                    "difficulty": "MEDIUM",
                    "points": 15,
                    "time_limit": 45
                }
            ]
        }, headers=headers)
        return r
    return _factory