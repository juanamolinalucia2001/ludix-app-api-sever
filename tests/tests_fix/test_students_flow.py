# tests/test_students_flow.py
import pytest

@pytest.mark.asyncio
async def test_estudiantes_registran_configuran_y_se_unen(client, teacher_headers, make_class, make_student):
    # Aula base
    aula = await make_class(teacher_headers, name="Aula Estudiantes")
    codigo = aula["class_code"]

    # 3 estudiantes
    ests = []
    for nm, av, pet in [("María", "/avatars/a1.png", "gato"),
                        ("Carlos", "/avatars/a2.png", "perro"),
                        ("Sofía", "/avatars/a3.png", "dino")]:
        e = await make_student(name=nm, avatar=av, mascot=pet)
        # unir a clase
        jo = await client.post("/classes/join", json={"class_code": codigo}, headers=e["headers"])
        assert jo.status_code == 200, jo.text
        ests.append(e)

    # cada uno puede ver juegos / sesiones (endpoints opcionales)
    for e in ests:
        gj = await client.get("/games/", headers=e["headers"])
        assert gj.status_code in (200, 404)
        ss = await client.get("/games/sessions", headers=e["headers"])
        assert ss.status_code in (200, 404)
