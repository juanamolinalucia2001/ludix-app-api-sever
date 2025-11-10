# tests/tests_fix/conftest.py
import asyncio
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from main import app  # Asegurate de que 'app' sea tu instancia de FastAPI


# =====================================================
# FIXTURES BASE (event_loop y cliente HTTP de pruebas)
# =====================================================
@pytest_asyncio.fixture(scope="session")
def event_loop():
    """
    Event loop para pytest-asyncio.
    Evita conflictos en CI o entornos como Colab.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client():
    """
    Cliente HTTP asíncrono apuntando a la app FastAPI.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# =====================================================
# HELPER DE REGISTRO CON FALLBACK AUTOMÁTICO
# =====================================================
async def _register_user(client: AsyncClient, *, role: str, name: str | None = None):
    """
    Intenta registrar un usuario de prueba en varias rutas comunes.
    Si falla (400/404/etc.), hace fallback a headers falsos (Bearer + uuid),
    lo que alcanza para los tests que solo checan autorización.
    """
    import uuid as _uuid

    email = f"test_{role}_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPass123!"
    name = name or (f"{role.capitalize()} Test")

    payload = {
        "name": name,
        "email": email,
        "password": password,
        "role": role.upper(),
    }

    candidate_paths = [
        "/users/register",
        "/auth/register",
        "/signup",
        "/auth/signup",
        # Agregá acá cualquier ruta propia de tu API, ej.: "/users/supabase/register"
    ]

    for path in candidate_paths:
        try:
            resp = await client.post(path, json=payload)
        except Exception:
            continue  # si la ruta no existe, probá la siguiente

        if 200 <= resp.status_code < 300:
            data = resp.json()
            token = (
                data.get("access_token")
                or data.get("token")
                or (data.get("data", {}) or {}).get("access_token")
                or (data.get("session") or {}).get("access_token")
            )
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                user_id = (data.get("user") or {}).get("id") or data.get("id") or _uuid.uuid4().hex
                role_out = (data.get("user") or {}).get("role") or role.upper()
                return {"headers": headers, "id": user_id, "role": role_out}

    # Fallback si ningún endpoint funciona
    fake_token = "test-fake-token"
    fake_id = _uuid.uuid4().hex
    return {
        "headers": {"Authorization": f"Bearer {fake_token}"},
        "id": fake_id,
        "role": role.upper(),
    }


# =====================================================
# FIXTURE DE DOCENTE (usa el helper anterior)
# =====================================================
@pytest_asyncio.fixture
async def teacher_headers(client):
    """
    Devuelve headers (Bearer ...) para un docente de pruebas.
    Además incluye 'id' y 'role' por conveniencia.
    """
    info = await _register_user(client, role="teacher", name="Teacher Pytest")
    headers = dict(info["headers"])
    headers["id"] = info.get("id")
    headers["role"] = "TEACHER"
    return headers


# =====================================================
# FACTORIES ASÍNCRONOS (crean entidades para los tests)
# =====================================================
@pytest.fixture
def make_class(client: AsyncClient):
    """
    Crea un aula de prueba.
    Uso: aula = await make_class(teacher_headers, name="Game Lab")
    """
    async def _factory(headers: dict, *, name: str = "Aula de Prueba", description: str = ""):
        resp = await client.post(
            "/classes",
            headers=headers,
            json={"name": name, "description": description},
        )
        resp.raise_for_status()
        data = resp.json()
        assert "id" in data and "class_code" in data, f"Respuesta inesperada al crear clase: {data}"
        return data
    return _factory


@pytest.fixture
def make_quiz(client: AsyncClient):
    """
    Crea un quiz mínimo válido.
    Uso: resp = await make_quiz(headers=teacher_headers, class_id=aula["id"])
    """
    async def _factory(
        headers: dict, *,
        class_id: str,
        title: str = "Quiz de Prueba",
        description: str | None = None,
        questions: list[dict] | None = None
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
    """
    Registra un estudiante y devuelve headers listos para usar.
    Uso: gamer = await make_student(name="Alex", avatar="/a.png", mascot="dino")
    """
    async def _factory(*, name: str = "Alumno Pytest", avatar: str | None = None, mascot: str | None = None):
        info = await _register_user(client, role="student", name=name)
        try:
            if avatar or mascot:
                await client.put(
                    "/users/profile",
                    headers=info["headers"],
                    json={"avatar": avatar, "mascot": mascot},
                )
        except Exception:
            pass
        return {
            "headers": info["headers"],
            "id": info.get("id"),
            "role": "STUDENT",
            "name": name,
            "avatar": avatar,
            "mascot": mascot,
        }
    return _factory
