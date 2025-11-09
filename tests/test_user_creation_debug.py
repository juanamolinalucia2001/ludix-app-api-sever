"""
Test específico para debuggear el problema de registro de usuarios
"""

import pytest
from services.supabase_service import supabase_service
import asyncio

class TestUserCreation:
    """Test específico para crear usuarios"""
    
    @pytest.mark.asyncio
    async def test_create_user_debug(self):
        """Test específico para crear usuario y ver el error exacto"""
        print("\n🔍 === DEBUG CREACIÓN DE USUARIO ===")
        
        try:
            # Intentar crear usuario
            user = await supabase_service.create_user(
                email="test_debug@ludix.com",
                password="TestPassword123!",
                name="Usuario Debug",
                role="student"
            )
            
            print(f"✅ Usuario creado exitosamente: {user}")
            
        except Exception as e:
            print(f"❌ Error creando usuario: {e}")
            print(f"📝 Tipo de error: {type(e).__name__}")
            
            # Intentar obtener más detalles del error
            if hasattr(e, 'details'):
                print(f"🔍 Detalles: {e.details}")
            
            if hasattr(e, 'message'):
                print(f"🔍 Mensaje: {e.message}")

if __name__ == "__main__":
    # Ejecutar test
    test = TestUserCreation()
    asyncio.run(test.test_create_user_debug())
