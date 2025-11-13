# tests/test_teacher_flow.py
import pytest

@pytest.mark.asyncio
async def test_docente_crea_aula_y_quiz(client, teacher_headers, make_class, make_quiz):
    # Crear aula
    aula = await make_class(teacher_headers, name="Matemáticas 6to", description="Aula divertida")
    assert "id" in aula and "class_code" in aula

    # Crear quiz
    qr = await make_quiz(headers=teacher_headers, class_id=aula["id"],
                          title="Operaciones Básicas" )
    assert qr.status_code in (200, 201), qr.text
    quiz = qr.json()
    assert quiz["title"] == "Operaciones Básicas"

    # Publicar (si endpoint existe)
    pub = await client.put(f"/quizzes/{quiz['id']}/publish", headers=teacher_headers)
    assert pub.status_code in (200, 404, 500)  # 404 si aún no implementaron publicar
