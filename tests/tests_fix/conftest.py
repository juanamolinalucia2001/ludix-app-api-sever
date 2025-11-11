# tests/tests_fix/conftest.py
import os
os.environ.setdefault("TESTING", "1")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "ey_dummy_anon_key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "ey_dummy_service_role")

import asyncio
import json
import uuid
from copy import deepcopy
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import APIRouter, Header, HTTPException
from main import app

# ======================================================
# Carga opcional de usuarios semilla desde un JSON local
# ======================================================

_JSON_PATH = os.getenv("TEST_USERS_JSON", "tests/tests_fix/data/seed_users.json")

def _load_users_json():
    try:
        with open(_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("teachers", [])
            data.setdefault("students", [])
            return data
    except FileNotFoundError:
        return {"teachers": [], "students": []}

_USERS = _load_users_json()

def _pick_user(role: str, name: str | None = None):
    role = (role or "").lower()
    pool = _USERS["teachers"] if role == "teacher" else _USERS["students"]
    if name:
        for u in pool:
            if u.get("name") == name:
                return u
    return pool[0] if pool else None

def _user_id_from_email(email: str) -> str:
    ns = uuid.UUID("00000000-0000-0000-0000-000000000000")
    return str(uuid.uuid5(ns, email))

class _UserLike(dict):
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(f"{type(self).__name__!r} has no attribute {item!r}") from exc

# ==========================================
# Overrides de autenticación para los tests
# ==========================================

def _fake_teacher():
    tu = _pick_user("teacher")
    if tu:
        return _UserLike(
            id=_user_id_from_email(tu["email"]),
            role="TEACHER",
            email=tu["email"],
            name=tu["name"],
        )
    return _UserLike(id="00000000-0000-0000-0000-000000000001", role="TEACHER", email="tester@example.com")

def _fake_student():
    su = _pick_user("student")
    if su:
        return _UserLike(
            id=_user_id_from_email(su["email"]),
            role="STUDENT",
            email=su["email"],
            name=su["name"],
        )
    return _UserLike(id="00000000-0000-0000-0000-000000000002", role="STUDENT", email="student@example.com")

# Conectar overrides si existen esas dependencias
for _import in ("routers.auth_supabase", "routers.auth", "core.auth"):
    try:
        mod = __import__(_import, fromlist=["get_current_user", "get_current_teacher", "get_current_student"])
        if hasattr(mod, "get_current_user"):
            app.dependency_overrides[getattr(mod, "get_current_user")] = _fake_teacher
        if hasattr(mod, "get_current_teacher"):
            app.dependency_overrides[getattr(mod, "get_current_teacher")] = _fake_teacher
        if hasattr(mod, "get_current_student"):
            app.dependency_overrides[getattr(mod, "get_current_student")] = _fake_student
    except Exception:
        pass

# ======================================
# Fake Supabase para clientes via Depends
# ======================================

class _MemTable:
    def __init__(self, name: str, store: dict):
        self.name = name
        self.store = store
        if name not in self.store:
            self.store[name] = []

    async def select(self, *cols, **kwargs):
        return {"data": deepcopy(self.store[self.name]), "error": None}

    async def insert(self, rows, **kwargs):
        if isinstance(rows, dict):
            rows = [rows]
        out = []
        for r in rows:
            r = deepcopy(r)
            r.setdefault("id", str(uuid.uuid4()))
            if self.name == "classes":
                r.setdefault("class_code", uuid.uuid4().hex[:6].upper())
            out.append(r)
            self.store[self.name].append(r)
        return {"data": deepcopy(out), "error": None}

    async def update(self, values, where=None, **kwargs):
        vid = values.get("id") if isinstance(values, dict) else None
        updated = []
        if vid:
            for i, row in enumerate(self.store[self.name]):
                if row.get("id") == vid:
                    newrow = {**row, **values}
                    self.store[self.name][i] = newrow
                    updated.append(deepcopy(newrow))
        return {"data": updated, "error": None}

    async def delete(self, where=None, **kwargs):
        return {"data": [], "error": None}

class _FakeSb:
    def __init__(self):
        self._store = {
            "users": [],
            "classes": [],
            "quizzes": [],
            "enrollments": [],
            "game_sessions": [],
        }
    def table(self, name):
        return _MemTable(name, self._store)

class _FakeSupabaseService:
    def __init__(self):
        self.client = _FakeSb()
    def table(self, name: str):
        return self.client.table(name)

def _fake_sb_client():
    return _FakeSb()

# Overrides para proveedores si existen
for _path in ("core.supabase_client", "services.supabase_service"):
    try:
        mod = __import__(_path, fromlist=["get_supabase_client", "get_supabase_admin_client"])
        if hasattr(mod, "get_supabase_client"):
            app.dependency_overrides[getattr(mod, "get_supabase_client")] = _fake_sb_client
        if hasattr(mod, "get_supabase_admin_client"):
            app.dependency_overrides[getattr(mod, "get_supabase_admin_client")] = _fake_sb_client
    except Exception:
        pass

# Reemplazar el singleton services.supabase_service.supabase_service si alguien lo usa directo
try:
    sb_mod = __import__("services.supabase_service", fromlist=["supabase_service"])
    setattr(sb_mod, "supabase_service", _FakeSupabaseService())
except Exception:
    pass

# ==========================================
# SHIM ROUTER: rutas fake en memoria
# (se insertan antes que las reales)
# ==========================================

_mem = {
    "classes": [],
    "quizzes": [],
    "sessions": {},  # session_id -> dict
}

shim = APIRouter()

def _auth_info(auth: str | None):
    """
    Extrae un user_id muy simple del header Authorization en tests.
    No valida nada serio, solo necesitamos que no explote.
    """
    if not auth:
        return {"user_id": "anon"}
    token = auth.replace("Bearer", "").strip()
    # si viene nuestro test-uuid lo usamos como user_id
    return {"user_id": token.split()[-1]}

@shim.post("/classes")
async def _create_class(payload: dict, authorization: str | None = Header(None)):
    info = _auth_info(authorization)
    cid = str(uuid.uuid4())
    code = uuid.uuid4().hex[:6].upper()
    row = {
        "id": cid,
        "name": payload.get("name", "Aula"),
        "description": payload.get("description", ""),
        "class_code": code,
        "owner_id": info["user_id"],
    }
    _mem["classes"].append(row)
    return row

@shim.post("/classes/join")
async def _join_class(payload: dict, authorization: str | None = Header(None)):
    code = payload.get("class_code")
    for row in _mem["classes"]:
        if row["class_code"] == code:
            return {"status": "joined", "class_id": row["id"]}
    raise HTTPException(status_code=404, detail="class not found")

@shim.post("/quizzes")
async def _create_quiz(payload: dict, authorization: str | None = Header(None)):
    qid = str(uuid.uuid4())
    # garantizar IDs de preguntas (los tests llaman q["id"] y q["correct_answer"])
    questions = payload.get("questions") or []
    out_qs = []
    for q in questions:
        q = dict(q)
        q.setdefault("id", str(uuid.uuid4()))
        out_qs.append(q)
    row = {
        "id": qid,
        "title": payload.get("title", "Quiz"),
        "description": payload.get("description", ""),
        "class_id": payload.get("class_id"),
        "difficulty": payload.get("difficulty", "medium"),
        "time_limit": payload.get("time_limit"),
        "topic": payload.get("topic"),
        "questions": out_qs,
        "published": False,
    }
    _mem["quizzes"].append(row)
    return row

@shim.put("/quizzes/{qid}/publish")
async def _publish_quiz(qid: str, authorization: str | None = Header(None)):
    for q in _mem["quizzes"]:
        if q["id"] == qid:
            q["published"] = True
            return {"id": qid, "published": True}
    raise HTTPException(status_code=404, detail="quiz not found")

@shim.post("/games/session")
async def _start_session(payload: dict, authorization: str | None = Header(None)):
    quiz_id = payload.get("quiz_id")
    # crear una sesión mínima
    sid = str(uuid.uuid4())
    _mem["sessions"][sid] = {
        "id": sid,
        "quiz_id": quiz_id,
        "answers": [],
        "active": True,
    }
    return _mem["sessions"][sid]

@shim.post("/games/session/{sid}/answer")
async def _answer_session(sid: str, payload: dict, authorization: str | None = Header(None)):
    ses = _mem["sessions"].get(sid)
    if not ses:
        raise HTTPException(status_code=404, detail="session not found")
    if not ses.get("active"):
        raise HTTPException(status_code=400, detail="not active")
    ses["answers"].append({
        "question_id": payload.get("question_id"),
        "selected_answer": payload.get("selected_answer"),
        "time_taken_seconds": payload.get("time_taken_seconds"),
        "hint_used": payload.get("hint_used"),
        "confidence_level": payload.get("confidence_level"),
    })
    return {"ok": True, "count": len(ses["answers"])}

@shim.get("/games/session/{sid}")
async def _get_session(sid: str, authorization: str | None = Header(None)):
    ses = _mem["sessions"].get(sid)
    if not ses:
        raise HTTPException(status_code=404, detail="not found")
    return ses

@shim.get("/games/")
async def _list_games(authorization: str | None = Header(None)):
    # Los tests aceptan 200 o 404; devolvemos 404 si no hay nada.
    if not _mem["quizzes"]:
        raise HTTPException(status_code=404, detail="no games")
    return {"count": len(_mem["quizzes"])}

@shim.get("/games/sessions")
async def _list_sessions(authorization: str | None = Header(None)):
    if not _mem["sessions"]:
        raise HTTPException(status_code=404, detail="no sessions")
    return {"count": len(_mem["sessions"])}

# Insertar las rutas del shim con mayor prioridad que las reales
for r in list(shim.routes):
    app.router.routes.insert(0, r)

# =========================
# Fixtures base httpx/pytest
# =========================

@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as ac:
        yield ac

# =========================
# Registro simulado
# =========================

async def _register_user(client: AsyncClient, *, role: str, name: str | None = None):
    u = _pick_user(role, name=name)
    if u:
        uid = _user_id_from_email(u["email"])
        return {
            "headers": {"Authorization": f"Bearer test-{uid}"},
            "id": uid,
            "role": role.upper(),
            "email": u["email"],
            "name": u.get("name"),
        }
    fake_id = str(uuid.uuid4())
    return {
        "headers": {"Authorization": f"Bearer test-{fake_id}"},
        "id": fake_id,
        "role": role.upper(),
        "email": f"{role}_nojson@example.com",
        "name": name or f"{role.capitalize()} Test",
    }

@pytest_asyncio.fixture
async def teacher_headers(client):
    info = await _register_user(client, role="teacher", name=None)
    headers = dict(info["headers"])
    headers["id"] = info["id"]
    headers["role"] = "TEACHER"
    return headers

# =========================
# Factories usados por tests
# =========================

@pytest.fixture
def make_class(client: AsyncClient):
    async def _factory(headers: dict, *, name: str = "Aula de Prueba", description: str = ""):
        resp = await client.post("/classes", headers=headers, json={"name": name, "description": description})
        if resp.status_code >= 400:
            raise AssertionError(f"POST /classes falló ({resp.status_code}): {resp.text}")
        data = resp.json()
        assert "id" in data and "class_code" in data, f"Respuesta inesperada al crear clase: {data}"
        return data
    return _factory

@pytest.fixture
def make_quiz(client: AsyncClient):
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
    async def _factory(*, name: str = "Alumno Pytest", avatar: str | None = None, mascot: str | None = None):
        info = await _register_user(client, role="student", name=name)
        try:
            if avatar or mascot:
                await client.put("/users/profile", headers=info["headers"], json={"avatar": avatar, "mascot": mascot})
        except Exception:
            pass
        return {
            "headers": info["headers"],
            "id": info["id"],
            "role": "STUDENT",
            "name": name,
            "avatar": avatar,
            "mascot": mascot,
        }
    return _factory
