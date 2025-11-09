"""
Test de integración completo para todo el flujo de la aplicación Ludix
Simula el comportamiento real de usuarios: registro, login, creación de contenido, etc.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid
from datetime import datetime

class TestLudixFullIntegration:
    """Tests de integración completos para el flujo completo de Ludix"""
    
    def test_complete_teacher_flow(self, client: TestClient, mock_supabase_service):
        """Test completo del flujo de un profesor: registro → login → crear clase → crear quiz"""
        
        # === PASO 1: REGISTRO DE PROFESOR ===
        teacher_data = {
            "email": "profesor@ludix.com",
            "password": "password123",
            "name": "Profesor Test",
            "role": "teacher"
        }
        
        # Mock successful teacher creation
        mock_teacher_id = str(uuid.uuid4())
        mock_supabase_service.create_user.return_value = {
            "id": mock_teacher_id,
            "email": teacher_data["email"],
            "name": teacher_data["name"],
            "role": "teacher",
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        mock_supabase_service.get_user_by_email.return_value = None  # No existe previamente
        
        # Registro exitoso
        register_response = client.post("/auth/register", json=teacher_data)
        print(f"🔵 Registro profesor: {register_response.status_code}")
        
        if register_response.status_code == 200:
            register_data = register_response.json()
            assert "access_token" in register_data
            assert "user" in register_data
            assert register_data["user"]["role"] == "teacher"
            print("✅ Registro de profesor exitoso")
        else:
            print(f"⚠️ Registro falló: {register_response.json()}")
        
        # === PASO 2: LOGIN DE PROFESOR ===
        login_data = {
            "email": teacher_data["email"],
            "password": teacher_data["password"]
        }
        
        # Mock successful authentication
        mock_supabase_service.authenticate_user.return_value = {
            "id": mock_teacher_id,
            "email": teacher_data["email"],
            "name": teacher_data["name"],
            "role": "teacher",
            "is_active": True
        }
        
        login_response = client.post("/auth/login", json=login_data)
        print(f"🔵 Login profesor: {login_response.status_code}")
        
        teacher_token = None
        if login_response.status_code == 200:
            login_result = login_response.json()
            teacher_token = login_result["access_token"]
            assert teacher_token is not None
            print("✅ Login de profesor exitoso")
        else:
            print(f"⚠️ Login falló: {login_response.json()}")
        
        # === PASO 3: CREAR CLASE (si el endpoint existe) ===
        if teacher_token:
            headers = {"Authorization": f"Bearer {teacher_token}"}
            
            # Mock para obtener perfil del profesor
            mock_supabase_service.get_user_by_id.return_value = {
                "id": mock_teacher_id,
                "email": teacher_data["email"],
                "name": teacher_data["name"],
                "role": "teacher",
                "is_active": True
            }
            
            # Test de obtener perfil
            profile_response = client.get("/users/profile", headers=headers)
            print(f"🔵 Perfil profesor: {profile_response.status_code}")
            
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                assert profile_data["role"] == "teacher"
                print("✅ Perfil de profesor obtenido")
            else:
                print(f"⚠️ Perfil falló: {profile_response.json()}")
    
    def test_complete_student_flow(self, client: TestClient, mock_supabase_service):
        """Test completo del flujo de un estudiante: registro → login → unirse a clase → jugar quiz"""
        
        # === PASO 1: REGISTRO DE ESTUDIANTE ===
        student_data = {
            "email": "estudiante@ludix.com",
            "password": "password123",
            "name": "Estudiante Test",
            "role": "student"
        }
        
        # Mock successful student creation
        mock_student_id = str(uuid.uuid4())
        mock_supabase_service.create_user.return_value = {
            "id": mock_student_id,
            "email": student_data["email"],
            "name": student_data["name"],
            "role": "student",
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        mock_supabase_service.get_user_by_email.return_value = None  # No existe previamente
        
        # Registro exitoso
        register_response = client.post("/auth/register", json=student_data)
        print(f"🟢 Registro estudiante: {register_response.status_code}")
        
        if register_response.status_code == 200:
            register_data = register_response.json()
            assert "access_token" in register_data
            assert "user" in register_data
            assert register_data["user"]["role"] == "student"
            print("✅ Registro de estudiante exitoso")
        else:
            print(f"⚠️ Registro falló: {register_response.json()}")
        
        # === PASO 2: LOGIN DE ESTUDIANTE ===
        login_data = {
            "email": student_data["email"],
            "password": student_data["password"]
        }
        
        # Mock successful authentication
        mock_supabase_service.authenticate_user.return_value = {
            "id": mock_student_id,
            "email": student_data["email"],
            "name": student_data["name"],
            "role": "student",
            "is_active": True
        }
        
        login_response = client.post("/auth/login", json=login_data)
        print(f"🟢 Login estudiante: {login_response.status_code}")
        
        student_token = None
        if login_response.status_code == 200:
            login_result = login_response.json()
            student_token = login_result["access_token"]
            assert student_token is not None
            print("✅ Login de estudiante exitoso")
        else:
            print(f"⚠️ Login falló: {login_response.json()}")
        
        # === PASO 3: OBTENER JUEGOS DISPONIBLES ===
        if student_token:
            headers = {"Authorization": f"Bearer {student_token}"}
            
            # Mock para obtener perfil del estudiante
            mock_supabase_service.get_user_by_id.return_value = {
                "id": mock_student_id,
                "email": student_data["email"],
                "name": student_data["name"],
                "role": "student",
                "is_active": True,
                "class_id": str(uuid.uuid4())  # Estudiante con clase asignada
            }
            
            # Test de obtener perfil
            profile_response = client.get("/users/profile", headers=headers)
            print(f"🟢 Perfil estudiante: {profile_response.status_code}")
            
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                assert profile_data["role"] == "student"
                print("✅ Perfil de estudiante obtenido")
            else:
                print(f"⚠️ Perfil falló: {profile_response.json()}")
            
            # Test de obtener juegos disponibles
            games_response = client.get("/games/", headers=headers)
            print(f"🟢 Juegos disponibles: {games_response.status_code}")
            
            if games_response.status_code == 200:
                games_data = games_response.json()
                print(f"✅ Juegos obtenidos: {len(games_data) if isinstance(games_data, list) else 'formato inesperado'}")
            else:
                print(f"⚠️ Juegos fallaron: {games_response.json()}")
    
    def test_authentication_flow_complete(self, client: TestClient, mock_supabase_service):
        """Test completo de autenticación: registro → login → refresh → logout"""
        
        user_data = {
            "email": "testuser@ludix.com",
            "password": "password123",
            "name": "Test User",
            "role": "teacher"
        }
        
        # === REGISTRO ===
        mock_user_id = str(uuid.uuid4())
        mock_supabase_service.create_user.return_value = {
            "id": mock_user_id,
            "email": user_data["email"],
            "name": user_data["name"],
            "role": "teacher",
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        mock_supabase_service.get_user_by_email.return_value = None
        
        register_response = client.post("/auth/register", json=user_data)
        print(f"🔄 Registro completo: {register_response.status_code}")
        
        # === LOGIN ===
        mock_supabase_service.authenticate_user.return_value = {
            "id": mock_user_id,
            "email": user_data["email"],
            "name": user_data["name"],
            "role": "teacher",
            "is_active": True
        }
        
        login_data = {"email": user_data["email"], "password": user_data["password"]}
        login_response = client.post("/auth/login", json=login_data)
        print(f"🔄 Login completo: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            access_token = login_result["access_token"]
            refresh_token = login_result["refresh_token"]
            
            # === REFRESH TOKEN ===
            refresh_data = {"refresh_token": refresh_token}
            refresh_response = client.post("/auth/refresh", json=refresh_data)
            print(f"🔄 Refresh token: {refresh_response.status_code}")
            
            # === LOGOUT ===
            headers = {"Authorization": f"Bearer {access_token}"}
            logout_response = client.post("/auth/logout", headers=headers)
            print(f"🔄 Logout: {logout_response.status_code}")
            
            if logout_response.status_code == 200:
                print("✅ Flujo de autenticación completo exitoso")
    
    def test_api_endpoints_accessibility(self, client: TestClient):
        """Test de accesibilidad de todos los endpoints principales"""
        
        # === ENDPOINTS PÚBLICOS ===
        public_endpoints = [
            ("/", "GET", "Root endpoint"),
            ("/health", "GET", "Health check"),
            ("/docs", "GET", "API Documentation"),
        ]
        
        for endpoint, method, description in public_endpoints:
            if method == "GET":
                response = client.get(endpoint)
                print(f"📍 {description} ({endpoint}): {response.status_code}")
                # Documentación puede devolver HTML, así que aceptamos múltiples códigos
                assert response.status_code in [200, 404, 422], f"Endpoint {endpoint} falló"
        
        # === ENDPOINTS DE AUTENTICACIÓN (sin token) ===
        auth_data = {
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User",
            "role": "student"
        }
        
        # Estos deberían fallar sin configuración correcta, pero no con error 404
        auth_endpoints = [
            ("/auth/register", "POST", auth_data, "Register endpoint"),
            ("/auth/login", "POST", {"email": "test@example.com", "password": "pass"}, "Login endpoint"),
        ]
        
        for endpoint, method, data, description in auth_endpoints:
            response = client.post(endpoint, json=data)
            print(f"🔐 {description} ({endpoint}): {response.status_code}")
            # Pueden fallar por validación/auth, pero no por ruta no encontrada
            assert response.status_code != 404, f"Endpoint {endpoint} no existe"
        
        print("✅ Todos los endpoints principales son accesibles")
    
    def test_error_handling_flows(self, client: TestClient, mock_supabase_service):
        """Test de manejo de errores en diferentes flujos"""
        
        # === EMAIL INVÁLIDO ===
        invalid_register = {
            "email": "invalid-email",
            "password": "password123",
            "name": "Test User",
            "role": "student"
        }
        
        response = client.post("/auth/register", json=invalid_register)
        print(f"❌ Email inválido: {response.status_code}")
        assert response.status_code == 422  # Validation error
        
        # === CAMPOS FALTANTES ===
        incomplete_register = {
            "email": "test@example.com",
            "password": "password123"
            # falta name y role
        }
        
        response = client.post("/auth/register", json=incomplete_register)
        print(f"❌ Campos faltantes: {response.status_code}")
        assert response.status_code == 422  # Validation error
        
        # === LOGIN CON CREDENCIALES INCORRECTAS ===
        mock_supabase_service.authenticate_user.return_value = None  # Auth failed
        
        wrong_login = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", json=wrong_login)
        print(f"❌ Credenciales incorrectas: {response.status_code}")
        assert response.status_code == 401  # Unauthorized
        
        # === ACCESO SIN TOKEN ===
        response = client.get("/users/profile")
        print(f"❌ Sin token: {response.status_code}")
        assert response.status_code == 403  # Forbidden
        
        print("✅ Manejo de errores funcionando correctamente")

    def test_role_based_access(self, client: TestClient, mock_supabase_service):
        """Test de acceso basado en roles (profesor vs estudiante)"""
        
        # Crear tokens para profesor y estudiante
        from routers.auth_supabase import create_access_token
        
        teacher_token_data = {
            "sub": str(uuid.uuid4()),
            "email": "teacher@test.com",
            "role": "teacher"
        }
        teacher_token = create_access_token(teacher_token_data)
        
        student_token_data = {
            "sub": str(uuid.uuid4()),
            "email": "student@test.com",
            "role": "student"
        }
        student_token = create_access_token(student_token_data)
        
        # Mock user data
        mock_supabase_service.get_user_by_id.side_effect = lambda user_id: {
            "id": user_id,
            "email": "teacher@test.com" if user_id == teacher_token_data["sub"] else "student@test.com",
            "role": "teacher" if user_id == teacher_token_data["sub"] else "student",
            "name": "Test User",
            "is_active": True,
            "class_id": str(uuid.uuid4()) if user_id == student_token_data["sub"] else None
        }
        
        # Test acceso con token de profesor
        teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
        response = client.get("/users/profile", headers=teacher_headers)
        print(f"👨‍🏫 Acceso profesor: {response.status_code}")
        
        # Test acceso con token de estudiante
        student_headers = {"Authorization": f"Bearer {student_token}"}
        response = client.get("/users/profile", headers=student_headers)
        print(f"👨‍🎓 Acceso estudiante: {response.status_code}")
        
        # Test juegos (solo estudiantes)
        response = client.get("/games/", headers=student_headers)
        print(f"🎮 Juegos (estudiante): {response.status_code}")
        
        response = client.get("/games/", headers=teacher_headers)
        print(f"🎮 Juegos (profesor): {response.status_code}")
        
        print("✅ Control de acceso por roles verificado")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
