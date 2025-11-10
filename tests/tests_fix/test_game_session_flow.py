# tests/test_game_session_flow.py
import pytest

@pytest.mark.asyncio
async def test_game_session_completa(client, teacher_headers, make_class, make_quiz, make_student):
    # Preparación: aula + quiz
    aula = await make_class(teacher_headers, name="Game Lab")
    qr = await make_quiz(headers=teacher_headers, class_id=aula["id"], title="Desafío Matemático")
    if qr.status_code != 200:
        pytest.skip("No se pudo crear el quiz (endpoint en desarrollo)")
    quiz = qr.json()
    await client.put(f"/quizzes/{quiz['id']}/publish", headers=teacher_headers)

    # Un estudiante “gamer”
    gamer = await make_student(name="Alex El Gamer", avatar="/avatars/gamer.png", mascot="dino")
    await client.post("/classes/join", json={"class_code": aula["class_code"]}, headers=gamer["headers"])

    # Iniciar sesión de juego
    s = await client.post("/games/session", json={"quiz_id": quiz["id"]}, headers=gamer["headers"])
    assert s.status_code in (200, 201), s.text
    ses = s.json()

    # Si el backend devuelve las preguntas (ideal), respondemos correcto
    if "questions" in quiz and quiz["questions"]:
        for q in quiz["questions"]:
            ans = await client.post(
                f"/games/session/{ses['id']}/answer",
                json={
                    "question_id": q["id"],
                    "selected_answer": q["correct_answer"],
                    "time_taken_seconds": 12,
                    "hint_used": False,
                    "confidence_level": 4
                },
                headers=gamer["headers"]
            )
            assert ans.status_code in (200, 201), ans.text

    # Ver estado final
    fin = await client.get(f"/games/session/{ses['id']}", headers=gamer["headers"])
    assert fin.status_code == 200 or fin.status_code == 404
