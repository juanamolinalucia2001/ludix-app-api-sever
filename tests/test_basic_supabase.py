"""
Tests básicos para la API con Supabase
"""

import pytest
from fastapi.testclient import TestClient


class TestBasicSupabaseEndpoints:
    """Test suite para endpoints básicos de la API con Supabase"""
    
    def test_root_endpoint(self, client: TestClient):
        """Test endpoint raíz"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert "docs" in data
        assert "redoc" in data
        
        assert data["message"] == "Ludix API Server"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        assert data["docs"] == "/docs"
        assert data["redoc"] == "/redoc"
    
    def test_health_check_endpoint(self, client: TestClient):
        """Test endpoint de health check"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "service" in data
        
        assert data["status"] == "healthy"
        assert data["service"] == "ludix-api"
    
    def test_docs_endpoint_accessible(self, client: TestClient):
        """Test que el endpoint de documentación es accesible"""
        response = client.get("/docs")
        
        # Debería devolver HTML de la documentación de Swagger
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_endpoint_accessible(self, client: TestClient):
        """Test que el endpoint de ReDoc es accesible"""
        response = client.get("/redoc")
        
        # Debería devolver HTML de la documentación de ReDoc
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_openapi_json_endpoint(self, client: TestClient):
        """Test que el esquema OpenAPI es accesible"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        openapi_schema = response.json()
        assert "openapi" in openapi_schema
        assert "info" in openapi_schema
        assert openapi_schema["info"]["title"] == "Ludix API Server"
        assert openapi_schema["info"]["version"] == "1.0.0"
    
    def test_invalid_endpoint_404(self, client: TestClient):
        """Test que endpoints inexistentes devuelven 404"""
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Not Found" in data["detail"]
    
    def test_method_not_allowed(self, client: TestClient):
        """Test método HTTP no permitido"""
        # El endpoint root solo acepta GET
        response = client.post("/")
        
        assert response.status_code == 405
        data = response.json()
        assert "detail" in data
        assert "Method Not Allowed" in data["detail"]


class TestSupabaseConfiguration:
    """Test para verificar configuración de Supabase"""
    
    def test_supabase_settings_loaded(self):
        """Test que la configuración de Supabase se carga"""
        from core.config import settings
        
        # Verificar que las variables existen
        assert hasattr(settings, 'SUPABASE_URL')
        assert hasattr(settings, 'SUPABASE_KEY')
        assert hasattr(settings, 'SUPABASE_SERVICE_KEY')
        
        # Verificar que son strings
        assert isinstance(settings.SUPABASE_URL, str)
        assert isinstance(settings.SUPABASE_KEY, str)
        assert isinstance(settings.SUPABASE_SERVICE_KEY, str)
    
    def test_supabase_client_can_be_imported(self):
        """Test que el cliente de Supabase se puede importar"""
        try:
            from core.supabase_client import get_supabase_client, get_supabase_admin_client
            from services.supabase_service import supabase_service
            
            assert callable(get_supabase_client)
            assert callable(get_supabase_admin_client)
            assert supabase_service is not None
            
        except ImportError as e:
            pytest.fail(f"Cannot import Supabase components: {e}")
    
    def test_api_structure_with_supabase(self, client: TestClient):
        """Test que la estructura de la API es correcta con Supabase"""
        openapi_response = client.get("/openapi.json")
        openapi_schema = openapi_response.json()
        
        paths = openapi_schema.get("paths", {})
        
        # Verificar que existen endpoints de autenticación
        auth_endpoints = [path for path in paths.keys() if path.startswith("/auth")]
        assert len(auth_endpoints) > 0, "Auth endpoints not found"
        
        # Verificar endpoints específicos de auth
        expected_auth_paths = ["/auth/register", "/auth/login", "/auth/me", "/auth/logout"]
        for expected_path in expected_auth_paths:
            assert expected_path in paths, f"Missing auth endpoint: {expected_path}"


class TestErrorHandling:
    """Test para manejo de errores"""
    
    def test_validation_error_format(self, client: TestClient):
        """Test formato de errores de validación"""
        # Enviar datos inválidos a un endpoint que los requiere
        response = client.post("/auth/register", json={
            "email": "invalid-email",  # Email malformado
            "password": "123",
            "name": "",  # Nombre vacío
            "role": "invalid"  # Rol inválido
        })
        
        assert response.status_code == 422
        error_data = response.json()
        
        assert "detail" in error_data
        # FastAPI devuelve una lista de errores de validación
        assert isinstance(error_data["detail"], list)
    
    def test_unauthorized_error_format(self, client: TestClient):
        """Test formato de errores de autorización"""
        # Intentar acceder a endpoint protegido sin token
        response = client.get("/auth/me")
        
        assert response.status_code == 403
        error_data = response.json()
        assert "detail" in error_data
    
    def test_invalid_token_error_format(self, client: TestClient):
        """Test formato de errores con token inválido"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
        error_data = response.json()
        assert "detail" in error_data


class TestPerformance:
    """Test básicos de rendimiento"""
    
    @pytest.mark.parametrize("endpoint", ["/", "/health", "/docs", "/redoc"])
    def test_endpoint_response_time(self, client: TestClient, endpoint: str):
        """Test que los endpoints básicos responden rápidamente"""
        import time
        
        start_time = time.time()
        response = client.get(endpoint)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Los endpoints básicos deberían responder en menos de 2 segundos
        assert response_time < 2.0, f"Endpoint {endpoint} took {response_time:.2f}s to respond"
        assert response.status_code == 200
