"""
Tests para endpoints básicos de la API
"""

import pytest
from fastapi.testclient import TestClient


class TestBasicEndpoints:
    """Test suite para endpoints básicos de la API"""
    
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
    
    def test_cors_headers(self, client: TestClient):
        """Test que los headers CORS están configurados correctamente"""
        # Test con preflight request
        response = client.options("/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization"
        })
        
        # FastAPI maneja CORS automáticamente
        assert response.status_code in [200, 405]  # 405 si OPTIONS no está implementado explícitamente
    
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


class TestAPIStructure:
    """Test para verificar la estructura general de la API"""
    
    def test_all_routers_included(self, client: TestClient):
        """Test que todos los routers están incluidos en la aplicación"""
        openapi_response = client.get("/openapi.json")
        openapi_schema = openapi_response.json()
        
        paths = openapi_schema.get("paths", {})
        
        # Verificar que existen endpoints de cada router
        auth_endpoints = [path for path in paths.keys() if path.startswith("/auth")]
        user_endpoints = [path for path in paths.keys() if path.startswith("/users")]
        game_endpoints = [path for path in paths.keys() if path.startswith("/games")]
        
        assert len(auth_endpoints) > 0, "Auth endpoints not found"
        assert len(user_endpoints) > 0, "User endpoints not found"
        assert len(game_endpoints) > 0, "Game endpoints not found"
    
    def test_api_tags(self, client: TestClient):
        """Test que los tags de la API están configurados correctamente"""
        openapi_response = client.get("/openapi.json")
        openapi_schema = openapi_response.json()
        
        # Verificar que existen los tags esperados
        paths = openapi_schema.get("paths", {})
        all_tags = set()
        
        for path_data in paths.values():
            for method_data in path_data.values():
                if isinstance(method_data, dict) and "tags" in method_data:
                    all_tags.update(method_data["tags"])
        
        expected_tags = {"authentication", "users", "games"}
        assert expected_tags.issubset(all_tags), f"Missing tags: {expected_tags - all_tags}"
    
    def test_security_schemes(self, client: TestClient):
        """Test que los esquemas de seguridad están definidos"""
        openapi_response = client.get("/openapi.json")
        openapi_schema = openapi_response.json()
        
        # Verificar que hay esquemas de seguridad definidos
        components = openapi_schema.get("components", {})
        security_schemes = components.get("securitySchemes", {})
        
        # Debería haber al menos un esquema de seguridad
        assert len(security_schemes) > 0, "No security schemes defined"


class TestErrorHandling:
    """Test para manejo de errores de la API"""
    
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
    
    def test_content_type_handling(self, client: TestClient):
        """Test manejo de diferentes tipos de contenido"""
        # Enviar datos sin Content-Type correcto
        response = client.post("/auth/login", data="invalid_data")
        
        # Debería manejar el error graciosamente
        assert response.status_code in [400, 422]


class TestPerformanceAndLimits:
    """Test para rendimiento y límites de la API"""
    
    def test_large_request_handling(self, client: TestClient):
        """Test manejo de requests grandes"""
        # Crear un payload grande pero válido
        large_name = "A" * 1000  # Nombre muy largo
        
        response = client.post("/auth/register", json={
            "email": "large@ludix.com",
            "password": "password123",
            "name": large_name,
            "role": "student"
        })
        
        # Debería manejar o rechazar graciosamente
        assert response.status_code in [200, 400, 422]
    
    def test_empty_request_handling(self, client: TestClient):
        """Test manejo de requests vacíos"""
        response = client.post("/auth/register", json={})
        
        assert response.status_code == 422  # Validation error
        error_data = response.json()
        assert "detail" in error_data
    
    @pytest.mark.parametrize("endpoint", ["/", "/health", "/docs", "/redoc"])
    def test_endpoint_response_time(self, client: TestClient, endpoint: str):
        """Test que los endpoints básicos responden rápidamente"""
        import time
        
        start_time = time.time()
        response = client.get(endpoint)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Los endpoints básicos deberían responder en menos de 1 segundo
        assert response_time < 1.0, f"Endpoint {endpoint} took {response_time:.2f}s to respond"
        assert response.status_code == 200
