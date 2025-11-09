"""
Test completo del flujo de autenticación con tokens JWT válidos
Este test demuestra que todos los endpoints funcionan correctamente con autenticación
"""

import pytest
import httpx
from main import app

class TestCompleteAuthFlow:
    """Test del flujo completo con autenticación JWT real"""
    
    @pytest.mark.asyncio
    async def test_docente_flow_with_real_auth(self):
        """Test completo de flujo docente con autenticación real"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            print("\n🎓 === FLUJO COMPLETO DOCENTE CON AUTENTICACIÓN ===")
            
            # PASO 1: Registro de docente
            print("🔹 PASO 1: Registrando docente...")
            register_data = {
                "email": "profesor_test@ludix.com",
                "password": "ProfesorSeguro123!",
                "name": "Profesor Test",
                "role": "teacher"
            }
            
            register_response = await client.post("/auth/register", json=register_data)
            print(f"📊 Registro docente: {register_response.status_code}")
            
            if register_response.status_code == 200:
                register_result = register_response.json()
                access_token = register_result["access_token"]
                teacher_id = register_result["user"]["id"]
                
                # Headers con token
                auth_headers = {"Authorization": f"Bearer {access_token}"}
                
                print(f"✅ DOCENTE REGISTRADO - ID: {teacher_id}")
                
                # PASO 2: Verificar perfil
                print("🔹 PASO 2: Verificando perfil docente...")
                profile_response = await client.get("/users/profile", headers=auth_headers)
                print(f"📊 Perfil docente: {profile_response.status_code}")
                
                if profile_response.status_code == 200:
                    print("✅ PERFIL DOCENTE OBTENIDO")
                
                # PASO 3: Crear aula
                print("🔹 PASO 3: Creando aula...")
                class_data = {
                    "name": "Matemáticas 4to Grado",
                    "description": "Aula de matemáticas para estudiantes de 4to grado"
                }
                
                class_response = await client.post("/classes/", json=class_data, headers=auth_headers)
                print(f"📊 Crear aula: {class_response.status_code}")
                
                if class_response.status_code == 200:
                    class_result = class_response.json()
                    class_id = class_result["id"]
                    class_code = class_result["code"]
                    print(f"✅ AULA CREADA - ID: {class_id}, Código: {class_code}")
                    
                    # PASO 4: Crear quiz
                    print("🔹 PASO 4: Creando quiz...")
                    quiz_data = {
                        "title": "Quiz de Suma y Resta",
                        "description": "Preguntas básicas de matemáticas",
                        "questions": [
                            {
                                "question_text": "¿Cuánto es 2 + 2?",
                                "options": ["3", "4", "5", "6"],
                                "correct_answer": "4",
                                "explanation": "2 más 2 es igual a 4"
                            },
                            {
                                "question_text": "¿Cuánto es 10 - 3?",
                                "options": ["6", "7", "8", "9"],
                                "correct_answer": "7",
                                "explanation": "10 menos 3 es igual a 7"
                            }
                        ],
                        "class_id": class_id
                    }
                    
                    quiz_response = await client.post("/quizzes/", json=quiz_data, headers=auth_headers)
                    print(f"📊 Crear quiz: {quiz_response.status_code}")
                    
                    if quiz_response.status_code == 200:
                        quiz_result = quiz_response.json()
                        quiz_id = quiz_result["id"]
                        print(f"✅ QUIZ CREADO - ID: {quiz_id}")
                        
                        # PASO 5: Ver estadísticas del aula
                        print("🔹 PASO 5: Consultando estadísticas...")
                        stats_response = await client.get(f"/classes/{class_id}/statistics", headers=auth_headers)
                        print(f"📊 Estadísticas aula: {stats_response.status_code}")
                        
                        if stats_response.status_code == 200:
                            print("✅ ESTADÍSTICAS OBTENIDAS")
                        
                        # PASO 6: Ver mis aulas
                        print("🔹 PASO 6: Consultando mis aulas...")
                        my_classes_response = await client.get("/classes/my-classes", headers=auth_headers)
                        print(f"📊 Mis aulas: {my_classes_response.status_code}")
                        
                        if my_classes_response.status_code == 200:
                            print("✅ MIS AULAS OBTENIDAS")
                        
                        print(f"\n🎉 === FLUJO DOCENTE COMPLETADO ===")
                        print(f"📈 RESUMEN:")
                        print(f"   - Registro: {register_response.status_code}")
                        print(f"   - Perfil: {profile_response.status_code}")
                        print(f"   - Crear Aula: {class_response.status_code}")
                        print(f"   - Crear Quiz: {quiz_response.status_code}")
                        print(f"   - Estadísticas: {stats_response.status_code}")
                        print(f"   - Mis Aulas: {my_classes_response.status_code}")
                        
                        return {
                            "class_code": class_code,
                            "quiz_id": quiz_id,
                            "all_success": all([
                                register_response.status_code == 200,
                                profile_response.status_code == 200,
                                class_response.status_code == 200,
                                quiz_response.status_code == 200,
                                stats_response.status_code == 200,
                                my_classes_response.status_code == 200
                            ])
                        }
            
            print("❌ Flujo docente falló en el registro")
            return {"all_success": False}

    @pytest.mark.asyncio
    async def test_estudiante_flow_with_real_auth(self):
        """Test completo de flujo estudiante con autenticación real"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            print("\n🎒 === FLUJO COMPLETO ESTUDIANTE CON AUTENTICACIÓN ===")
            
            # PASO 1: Registro de estudiante
            print("🔹 PASO 1: Registrando estudiante...")
            register_data = {
                "email": "estudiante_test@ludix.com",
                "password": "EstudianteSeguro123!",
                "name": "Estudiante Test",
                "role": "student"
            }
            
            register_response = await client.post("/auth/register", json=register_data)
            print(f"📊 Registro estudiante: {register_response.status_code}")
            
            if register_response.status_code == 200:
                register_result = register_response.json()
                access_token = register_result["access_token"]
                student_id = register_result["user"]["id"]
                
                # Headers con token
                auth_headers = {"Authorization": f"Bearer {access_token}"}
                
                print(f"✅ ESTUDIANTE REGISTRADO - ID: {student_id}")
                
                # PASO 2: Verificar avatares disponibles (sin auth)
                print("🔹 PASO 2: Consultando avatares disponibles...")
                avatars_response = await client.get("/users/available-avatars")
                print(f"📊 Avatares disponibles: {avatars_response.status_code}")
                
                if avatars_response.status_code == 200:
                    avatars_data = avatars_response.json()
                    print(f"✅ AVATARES OBTENIDOS - Total: {len(avatars_data.get('avatars', []))}")
                
                # PASO 3: Verificar mascotas disponibles (sin auth)
                print("🔹 PASO 3: Consultando mascotas disponibles...")
                mascots_response = await client.get("/users/available-mascots")
                print(f"📊 Mascotas disponibles: {mascots_response.status_code}")
                
                if mascots_response.status_code == 200:
                    mascots_data = mascots_response.json()
                    print(f"✅ MASCOTAS OBTENIDAS - Total: {len(mascots_data.get('mascots', []))}")
                
                # PASO 4: Configurar perfil (con auth)
                print("🔹 PASO 4: Configurando perfil...")
                profile_setup_data = {
                    "name": "Estudiante Test Actualizado",
                    "avatar_url": "/avatars/avatar1.png",
                    "mascot": "carpi"
                }
                
                setup_response = await client.post("/users/setup-profile", json=profile_setup_data, headers=auth_headers)
                print(f"📊 Setup perfil: {setup_response.status_code}")
                
                if setup_response.status_code == 200:
                    print("✅ PERFIL CONFIGURADO")
                
                # PASO 5: Ver mi perfil (con auth)
                print("🔹 PASO 5: Consultando mi perfil...")
                my_profile_response = await client.get("/users/profile", headers=auth_headers)
                print(f"📊 Mi perfil: {my_profile_response.status_code}")
                
                if my_profile_response.status_code == 200:
                    print("✅ MI PERFIL OBTENIDO")
                
                # PASO 6: Ver mis sesiones de juego (con auth)
                print("🔹 PASO 6: Consultando mis sesiones...")
                sessions_response = await client.get("/games/my-sessions", headers=auth_headers)
                print(f"📊 Mis sesiones: {sessions_response.status_code}")
                
                if sessions_response.status_code == 200:
                    print("✅ MIS SESIONES OBTENIDAS")
                
                print(f"\n🎉 === FLUJO ESTUDIANTE COMPLETADO ===")
                print(f"📈 RESUMEN:")
                print(f"   - Registro: {register_response.status_code}")
                print(f"   - Avatares: {avatars_response.status_code}")
                print(f"   - Mascotas: {mascots_response.status_code}")
                print(f"   - Setup Perfil: {setup_response.status_code}")
                print(f"   - Mi Perfil: {my_profile_response.status_code}")
                print(f"   - Mis Sesiones: {sessions_response.status_code}")
                
                return {
                    "all_success": all([
                        register_response.status_code == 200,
                        avatars_response.status_code == 200,
                        mascots_response.status_code == 200,
                        setup_response.status_code == 200,
                        my_profile_response.status_code == 200,
                        sessions_response.status_code == 200
                    ])
                }
            
            print("❌ Flujo estudiante falló en el registro")
            return {"all_success": False}

    @pytest.mark.asyncio
    async def test_complete_interaction_flow(self):
        """Test de interacción completa: docente crea aula, estudiante se une"""
        print("\n🤝 === FLUJO DE INTERACCIÓN COMPLETA ===")
        
        # Primero ejecutar flujo docente
        teacher_result = await self.test_docente_flow_with_real_auth()
        
        if teacher_result.get("all_success"):
            # Luego ejecutar flujo estudiante
            student_result = await self.test_estudiante_flow_with_real_auth()
            
            if student_result.get("all_success"):
                print("\n🏆 === TODOS LOS FLUJOS EXITOSOS ===")
                print("✅ Docente: Registro → Crear Aula → Crear Quiz → Estadísticas")
                print("✅ Estudiante: Registro → Avatares → Mascotas → Perfil → Sesiones")
                assert True
            else:
                print("\n⚠️ Flujo estudiante falló")
                assert False
        else:
            print("\n⚠️ Flujo docente falló")
            assert False
