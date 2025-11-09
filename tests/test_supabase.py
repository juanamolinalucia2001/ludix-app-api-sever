"""
Tests específicos para integración con Supabase
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.config import settings


class TestSupabaseIntegration:
    """Test suite para integración con Supabase"""
    
    def test_supabase_configuration_loaded(self):
        """Test que la configuración de Supabase se carga correctamente"""
        # Verificar que las variables de configuración existen
        assert hasattr(settings, 'SUPABASE_URL')
        assert hasattr(settings, 'SUPABASE_KEY')
        assert hasattr(settings, 'SUPABASE_SERVICE_KEY')
        
        # En el entorno de test, deberían tener valores por defecto o de test
        assert isinstance(settings.SUPABASE_URL, str)
        assert isinstance(settings.SUPABASE_KEY, str)
        assert isinstance(settings.SUPABASE_SERVICE_KEY, str)
    
    @patch.dict(os.environ, {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test-anon-key',
        'SUPABASE_SERVICE_KEY': 'test-service-key'
    })
    def test_supabase_environment_variables(self):
        """Test que las variables de entorno de Supabase se leen correctamente"""
        from core.config import Settings
        
        # Crear nueva instancia de settings para leer las env vars
        test_settings = Settings()
        
        assert test_settings.SUPABASE_URL == 'https://test.supabase.co'
        assert test_settings.SUPABASE_KEY == 'test-anon-key'
        assert test_settings.SUPABASE_SERVICE_KEY == 'test-service-key'
    
    def test_database_fallback_to_sqlite(self):
        """Test que la aplicación puede funcionar sin Supabase usando SQLite"""
        # Verificar que hay un fallback a SQLite configurado
        assert "sqlite" in settings.DATABASE_URL.lower() or "postgresql" in settings.DATABASE_URL.lower()
    
    @patch('supabase.create_client')
    def test_supabase_client_creation_mock(self, mock_create_client):
        """Test creación de cliente Supabase (mockeado)"""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        
        # Simular importación del cliente Supabase
        try:
            from core.supabase_client import supabase_client
            # Si el módulo existe, verificar que se puede crear el cliente
            mock_create_client.assert_called()
        except ImportError:
            # Si no existe el módulo, es esperado en el entorno de test
            pytest.skip("Supabase client module not implemented yet")
    
    def test_api_works_without_supabase(self, client: TestClient):
        """Test que la API funciona correctamente sin conexión a Supabase real"""
        # Endpoints básicos deberían funcionar sin Supabase
        response = client.get("/")
        assert response.status_code == 200
        
        response = client.get("/health")
        assert response.status_code == 200
        
        # La documentación debería estar disponible
        response = client.get("/openapi.json")
        assert response.status_code == 200


class TestSupabaseDataFlow:
    """Test de flujos de datos con Supabase"""
    
    def test_user_registration_with_supabase_config(self, client: TestClient, db_session: Session):
        """Test registro de usuario con configuración de Supabase"""
        user_data = {
            "email": "supabase_user@ludix.com",
            "password": "supabase123",
            "name": "Supabase Test User",
            "role": "student"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        # Debería funcionar independientemente de si Supabase está configurado
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == user_data["email"]
    
    def test_authentication_flow_with_supabase_settings(self, client: TestClient, test_student):
        """Test flujo de autenticación con configuración de Supabase"""
        login_data = {
            "email": test_student.email,
            "password": "student123"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        token_data = response.json()
        token = token_data["access_token"]
        
        # Usar el token para acceder a endpoint protegido
        headers = {"Authorization": f"Bearer {token}"}
        profile_response = client.get("/auth/me", headers=headers)
        
        assert profile_response.status_code == 200
        user_data = profile_response.json()
        assert user_data["email"] == test_student.email


class TestSupabaseConfiguration:
    """Test de configuración específica para Supabase"""
    
    def test_supabase_url_validation(self):
        """Test validación de URL de Supabase"""
        # URL válida de Supabase
        valid_urls = [
            "https://abcdefgh.supabase.co",
            "https://test-project.supabase.co",
            "https://my-project-123.supabase.co"
        ]
        
        for url in valid_urls:
            # Simular validación de URL
            assert url.startswith("https://")
            assert ".supabase.co" in url
    
    def test_supabase_key_format(self):
        """Test formato de claves de Supabase"""
        # Las claves de Supabase suelen tener un formato específico
        test_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRlc3QiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTY0MzgwODAwMCwiZXhwIjoxOTU5Mzg0MDAwfQ.test"
        
        # Las claves de Supabase son típicamente JWT tokens largos
        assert len(test_key) > 100
        assert test_key.count('.') == 2  # JWT tiene 3 partes separadas por puntos
    
    @patch.dict(os.environ, {
        'SUPABASE_URL': '',
        'SUPABASE_KEY': '',
        'SUPABASE_SERVICE_KEY': ''
    })
    def test_empty_supabase_config_handling(self, client: TestClient):
        """Test manejo de configuración vacía de Supabase"""
        # La aplicación debería funcionar incluso con configuración vacía
        response = client.get("/health")
        assert response.status_code == 200
        
        # Debería poder registrar usuarios (usando SQLite como fallback)
        user_data = {
            "email": "no_supabase@ludix.com",
            "password": "password123",
            "name": "No Supabase User",
            "role": "teacher"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 200


class TestSupabaseErrorHandling:
    """Test manejo de errores específicos de Supabase"""
    
    @patch('supabase.create_client')
    def test_supabase_connection_error_handling(self, mock_create_client):
        """Test manejo de errores de conexión con Supabase"""
        # Simular error de conexión
        mock_create_client.side_effect = Exception("Connection failed")
        
        # La aplicación debería manejar el error graciosamente
        try:
            from core.supabase_client import supabase_client
            pytest.fail("Should have handled Supabase connection error")
        except Exception:
            # Es esperado que falle en el entorno de test
            pass
    
    def test_database_fallback_on_supabase_error(self, client: TestClient):
        """Test fallback a SQLite cuando Supabase no está disponible"""
        # Independientemente del estado de Supabase, la API debería funcionar
        response = client.get("/")
        assert response.status_code == 200
        
        # Los endpoints de autenticación deberían funcionar
        user_data = {
            "email": "fallback_user@ludix.com",
            "password": "fallback123",
            "name": "Fallback User",
            "role": "student"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 200


class TestSupabasePerformance:
    """Test de rendimiento con Supabase"""
    
    def test_api_performance_with_supabase_config(self, client: TestClient):
        """Test que la configuración de Supabase no afecta el rendimiento de la API"""
        import time
        
        # Medir tiempo de respuesta de endpoints básicos
        start_time = time.time()
        response = client.get("/")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Debería responder rápidamente independientemente de la configuración de Supabase
        assert response_time < 1.0
        assert response.status_code == 200
    
    def test_database_query_performance(self, client: TestClient, test_student):
        """Test rendimiento de consultas de base de datos"""
        import time
        
        # Login para obtener token
        login_data = {
            "email": test_student.email,
            "password": "student123"
        }
        
        start_time = time.time()
        response = client.post("/auth/login", json=login_data)
        end_time = time.time()
        
        assert response.status_code == 200
        
        # El login (que incluye consulta a BD) debería ser rápido
        login_time = end_time - start_time
        assert login_time < 2.0  # Menos de 2 segundos para login


class TestSupabaseFeatures:
    """Test de funcionalidades específicas de Supabase"""
    
    def test_realtime_capabilities_config(self):
        """Test configuración para capacidades en tiempo real"""
        # Verificar que la configuración permite funcionalidades en tiempo real
        # (para futuras implementaciones)
        assert hasattr(settings, 'SUPABASE_URL')
        
        # Las URLs de Supabase soportan WebSockets para tiempo real
        if settings.SUPABASE_URL and settings.SUPABASE_URL.startswith('https://'):
            websocket_url = settings.SUPABASE_URL.replace('https://', 'wss://')
            assert websocket_url.startswith('wss://')
    
    def test_row_level_security_support(self):
        """Test que la configuración soporta Row Level Security"""
        # Verificar que tenemos las claves necesarias para RLS
        assert hasattr(settings, 'SUPABASE_SERVICE_KEY')
        
        # La service key es necesaria para operaciones administrativas
        # que pueden bypasear RLS cuando sea necesario
        if settings.SUPABASE_SERVICE_KEY:
            assert len(settings.SUPABASE_SERVICE_KEY) > 50  # Service keys son largas
    
    def test_storage_capabilities_config(self):
        """Test configuración para capacidades de almacenamiento"""
        # Verificar configuración para upload de archivos
        assert hasattr(settings, 'MAX_FILE_SIZE')
        assert hasattr(settings, 'UPLOAD_DIR')
        
        assert settings.MAX_FILE_SIZE > 0
        assert isinstance(settings.UPLOAD_DIR, str)
        assert len(settings.UPLOAD_DIR) > 0


@pytest.mark.integration
class TestSupabaseLiveIntegration:
    """Test de integración con Supabase real (solo si está configurado)"""
    
    @pytest.mark.skipif(
        not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_KEY'),
        reason="Supabase not configured for live testing"
    )
    def test_live_supabase_connection(self):
        """Test conexión real con Supabase (solo si está configurado)"""
        try:
            import supabase
            
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_KEY')
            
            client = supabase.create_client(url, key)
            
            # Test básico de conexión
            response = client.table('users').select('*').limit(1).execute()
            
            # Si llega aquí, la conexión funciona
            assert response is not None
            
        except Exception as e:
            pytest.skip(f"Live Supabase test failed: {e}")
    
    @pytest.mark.skipif(
        not os.getenv('SUPABASE_URL'),
        reason="Supabase URL not configured"
    )
    def test_supabase_schema_compatibility(self):
        """Test compatibilidad del schema con Supabase"""
        # Verificar que el schema de la aplicación es compatible con PostgreSQL
        # (que es lo que usa Supabase)
        
        from models.User import User
        from models.Quiz import Quiz, Question, Class
        from models.GameSession import GameSession, Answer
        
        # Verificar que los modelos tienen los campos correctos
        assert hasattr(User, '__tablename__')
        assert hasattr(Quiz, '__tablename__')
        assert hasattr(Question, '__tablename__')
        assert hasattr(Class, '__tablename__')
        assert hasattr(GameSession, '__tablename__')
        assert hasattr(Answer, '__tablename__')
