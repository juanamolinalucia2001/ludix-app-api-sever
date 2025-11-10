import os
import uuid
import pytest
import httpx
from typing import Dict
from main import app


@pytest.fixture
async def client():
    """Cliente HTTP asíncrono para los tests."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as c:
        yield c


@pytest.fixture
def uniq_email():
    def _make(prefix: str, domain="ludix.edu"):
        return f"{prefix}_{uuid.uuid4().hex[:8]}@{domain}"
    return _make


@pytest.fixture
async def teacher_headers(client, uniq_email):
    """Registra un docente y devuelve headers con Bearer token."""
    payload = {
        "email": uniq_email("teacher"),
        "password": "DocenteSeguro2024!",
        "name": "Prof. Test",
        "role": "teacher",
    }
    r = await client.post("/auth/register", json=payload)
    assert r.status_code in (200, 201), r.text
    data = r.json()
    token = data.get("access_token") or data.get("token")
    assert token, "No se recibió token en el registro/login"
    return {"Authorization": f"Bearer {token}"}


# 👇 Estas tres se vuelven async fixtures (para que el client sea awaitable)
@pytest.fixture
async def make_student(client, uniq_email):
    """Crea un estudiante con perfil listo."""
    async def _factory(name="Estudiante", avatar="/avatars/a1.png", mascot="gato"):
        payload = {
            "email": uniq_email("student", "estudiante.com"),
            "password": "Estudiante123!",
            "name": name,
            "role": "student",
        }
        r = await client.post("/auth/register", json=payload)
        assert r.status_code in (200, 201), r.text
        data = r.json()
        token = data.get("access_token") or data.get("token")
        headers = {"Authorization": f"Bearer {token}"}

        prof = await client.post("/users/setup-profile", json={
            "name": name, "avatar_url": avatar, "mascot": mascot
        }, headers=headers)
        assert prof.status_code in (200, 201), prof.text

        return {"user": data.get("user"), "headers": headers}

    return _factory


@pytest.fixture
async def make_class(client):
    """Crea una clase con los datos dados."""
    async def _factory(headers, name="Aula de Prueba", description="Aula demo", max_students=30):
        r = await client.post("/classes/", json={
            "name": name,
            "description": description,
            "max_students": max_students
        }, headers=headers)
        assert r.status_code in (200, 201), r.text
        return r.json()
    return _factory


@pytest.fixture
async def make_quiz(client):
    """Crea un quiz con preguntas de prueba."""
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
