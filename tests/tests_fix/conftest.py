# tests/tests_fix/conftest.py
import asyncio
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from main import app  # asegúrate de que 'app' sea la FastAPI real

# -------- Infra ----------
@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# -------- Helpers auth ----------
async def _register_user(client: AsyncClient, *, role: str, name: str | None = None):
    email = f"test_{role}_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPass123!"
    name = name or (f"{role.capitalize()} Test")

    resp = await client.post(
        "/users/register",
        json={"name": name, "email": email, "password": password, "role": role.upper()},
    )
    if resp.status_code >= 400:
        resp = await client.post(
            "/auth/register",
            json={"name": name, "email": email, "password": password, "role": role.upper()},
        )

    resp.raise_for_status()
    data = resp.json()

    token = (
        data.get("access_token")
        or data.get("token")
        or (data.get("data", {}) or {}).get("access_token")
        or (data.get("session") or {}).get("access_token")
    )
    assert token, f"No se pudo obtener access_token del registro: {data}"

    headers = {"Authorization": f"Bearer {token}"}
    user_id = (data.get("user") or {}).get("id") or data.get("id")
    role_out = (data.get("user") or {}).get("role") or role.upper()
    return {"headers": headers, "id": user_id, "role": role_out}

# -------- Fixtures de alto nivel ----------
@pytest_asyncio.fixture
async def teacher_headers(client):
    info = await _register_user(client, role="teacher", name="Teacher Pytest")
    headers = dict(info["headers"])
    headers["id"] = info.get("id")
    headers["role"] = "TEACHER"
    return headers

# -------- Factories (inyectan client) ----------
@pytest.fixture
def make_class(client: AsyncClient):
    async def _factory(headers: dict, *, name: str = "Aula de Prueba", description: str = ""):
        resp = await client.post("/classes", headers=headers, json={"name": name, "description": description})
        resp.raise_for_status()
        data = resp.json()
        assert "id" in data and "class_code" in data, f"Respuesta inesperada al crear clase: {data}"
        return data
    return _factory

@pytest.fixture
def make_quiz(client: AsyncClient):
    async def _factory(
        headers: dict, *, class_id: str, title: str = "Quiz de Prueba",
        description: str | None = None, questions: list[dict] | None = None
    ):
        default_questions = [
            {
                "question_text": "¿Cuánto es 15 + 27?",
                "question_type": "multiple_choice",
                "options": ["32", "42", "40", "38"],
                "correct_answer": 1,
                "difficulty": "medium",
                "points": 10,
                "time_limit": 30,
            },
            {
                "question_text": "¿Cuánto es 8 × 7?",
                "question_type": "multiple_choice",
                "options": ["54", "56", "64", "48"],
                "correct_answer": 1,
                "difficulty": "easy",
                "points": 10,
                "time_limit": 30,
            },
        ]
        payload = {
            "title": title,
            "description": description or "",
            "class_id": class_id,
            "difficulty": "medium",
            "time_limit": None,
            "topic": None,
            "questions": questions or default_questions,
        }
        return await client.post("/quizzes", headers=headers, json=payload)
    return _factory

@pytest.fixture
def make_student(client: AsyncClient):
    async def _factory(*, name: str = "Alumno Pytest", avatar: str | None = None, mascot: str | None = None):
        info = await _register_user(client, role="student", name=name)
        try:
            if avatar or mascot:
                await client.put("/users/profile", headers=info["headers"], json={"avatar": avatar, "mascot": mascot})
        except Exception:
            pass
        return {"headers": info["headers"], "id": info.get("id"), "role": "STUDENT", "name": name,
                "avatar": avatar, "mascot": mascot}
    return _factory
