"""
Test de diagnóstico para verificar conexión y permisos de Supabase
"""

import pytest
from core.supabase_client import get_supabase_client, get_supabase_admin_client
from services.supabase_service import supabase_service
import asyncio

class TestSupabaseDiagnostic:
    """Diagnóstico de conexión y permisos con Supabase"""
    
    def test_supabase_connection(self):
        """Test básico de conexión a Supabase"""
        print("\n🔍 === DIAGNÓSTICO DE SUPABASE ===")
        
        try:
            # Test cliente regular
            client = get_supabase_client()
            print(f"✅ Cliente regular obtenido: {type(client)}")
            
            # Test cliente admin
            admin_client = get_supabase_admin_client()
            print(f"✅ Cliente admin obtenido: {type(admin_client)}")
            
            print("✅ Conexiones establecidas correctamente")
            
        except Exception as e:
            print(f"❌ Error en conexión: {e}")
            pytest.fail(f"Failed to connect to Supabase: {e}")
    
    @pytest.mark.asyncio
    async def test_simple_database_query(self):
        """Test de consulta simple a la base de datos"""
        print("\n🔍 === TEST DE CONSULTA SIMPLE ===")
        
        try:
            client = get_supabase_client()
            
            # Intentar una consulta muy básica
            result = client.table("users").select("*").limit(1).execute()
            print(f"📊 Consulta exitosa - Datos: {len(result.data) if result.data else 0} registros")
            print(f"✅ Conexión a tabla 'users' funciona")
            
        except Exception as e:
            print(f"❌ Error en consulta: {e}")
            print(f"📝 Detalles del error: {type(e).__name__}")
    
    @pytest.mark.asyncio
    async def test_user_creation_direct(self):
        """Test directo de creación de usuario con admin client"""
        print("\n🔍 === TEST DE CREACIÓN DIRECTA ===")
        
        try:
            admin_client = get_supabase_admin_client()
            
            # Test de autenticación con admin client
            test_email = "test_diagnostico@ludix.com"
            
            # Intentar crear usuario directamente
            auth_response = admin_client.auth.admin.create_user({
                "email": test_email,
                "password": "TestPassword123!",
                "email_confirm": True
            })
            
            if auth_response.user:
                user_id = auth_response.user.id
                print(f"✅ Usuario creado en Auth - ID: {user_id}")
                
                # Intentar insertar en tabla users
                user_data = {
                    "id": user_id,
                    "email": test_email,
                    "full_name": "Test Diagnóstico",
                    "role": "student"
                }
                
                table_result = admin_client.table("users").insert(user_data).execute()
                
                if table_result.data:
                    print(f"✅ Usuario insertado en tabla - Data: {table_result.data[0]}")
                    
                    # Limpiar: eliminar usuario de prueba
                    admin_client.auth.admin.delete_user(user_id)
                    print("🧹 Usuario de prueba eliminado")
                    
                    return True
                else:
                    print(f"❌ Error insertando en tabla: {table_result}")
            else:
                print(f"❌ Error creando usuario en Auth: {auth_response}")
                
        except Exception as e:
            print(f"❌ Error en creación directa: {e}")
            print(f"📝 Detalles: {type(e).__name__}")
            return False
    
    @pytest.mark.asyncio
    async def test_supabase_service_methods(self):
        """Test de métodos del servicio Supabase"""
        print("\n🔍 === TEST DE MÉTODOS DEL SERVICIO ===")
        
        try:
            # Test método get_user_by_email (que falla en los tests)
            result = await supabase_service.get_user_by_email("nonexistent@test.com")
            print(f"📊 get_user_by_email result: {result}")
            print("✅ Método get_user_by_email funciona (None es válido para email inexistente)")
            
        except Exception as e:
            print(f"❌ Error en get_user_by_email: {e}")
            print(f"📝 Tipo de error: {type(e).__name__}")
    
    @pytest.mark.asyncio
    async def test_table_permissions(self):
        """Test de permisos en tablas"""
        print("\n🔍 === TEST DE PERMISOS EN TABLAS ===")
        
        tables = ["users", "classes", "quizzes", "game_sessions"]
        
        client = get_supabase_client()
        admin_client = get_supabase_admin_client()
        
        for table in tables:
            try:
                # Test con cliente regular
                regular_result = client.table(table).select("*").limit(1).execute()
                print(f"📊 Tabla '{table}' - Cliente regular: {len(regular_result.data) if regular_result.data else 0} registros")
                
                # Test con cliente admin
                admin_result = admin_client.table(table).select("*").limit(1).execute()
                print(f"📊 Tabla '{table}' - Cliente admin: {len(admin_result.data) if admin_result.data else 0} registros")
                
            except Exception as e:
                print(f"❌ Error en tabla '{table}': {e}")

if __name__ == "__main__":
    # Ejecutar tests de diagnóstico
    diagnostic = TestSupabaseDiagnostic()
    
    print("🚀 Iniciando diagnóstico de Supabase...")
    
    # Test síncrono
    diagnostic.test_supabase_connection()
    
    # Tests asíncronos
    asyncio.run(diagnostic.test_simple_database_query())
    asyncio.run(diagnostic.test_user_creation_direct())
    asyncio.run(diagnostic.test_supabase_service_methods())
    asyncio.run(diagnostic.test_table_permissions())
    
    print("\n🏁 Diagnóstico completado")
