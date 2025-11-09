"""
Test para verificar qué está bloqueando el registro
"""

import asyncio
from services.supabase_service import supabase_service
import uuid

async def debug_registration():
    print("🔍 === DEBUGGING REGISTRO ===")
    
    # Test 1: Intentar solo insertar en tabla users (sin Auth)
    print("\n1️⃣ Probando inserción directa en tabla users...")
    try:
        user_id = str(uuid.uuid4())
        user_data = {
            "id": user_id,
            "email": "direct_test@ludix.com",
            "name": "Direct Test",
            "role": "STUDENT",
            "is_active": True
        }
        
        result = supabase_service.admin_client.table("users").insert(user_data).execute()
        print(f"✅ Inserción directa exitosa: {result.data}")
        
        # Limpiar
        supabase_service.admin_client.table("users").delete().eq("id", user_id).execute()
        print("🧹 Usuario de prueba eliminado")
        
    except Exception as e:
        print(f"❌ Error en inserción directa: {e}")
    
    # Test 2: Intentar solo crear en Supabase Auth
    print("\n2️⃣ Probando creación solo en Supabase Auth...")
    try:
        auth_response = supabase_service.admin_client.auth.admin.create_user({
            "email": "auth_only_test@ludix.com",
            "password": "TestPassword123!",
            "email_confirm": True
        })
        
        if auth_response.user:
            print(f"✅ Usuario Auth creado: {auth_response.user.id}")
            
            # Limpiar
            supabase_service.admin_client.auth.admin.delete_user(auth_response.user.id)
            print("🧹 Usuario Auth eliminado")
        else:
            print("❌ No se pudo crear usuario en Auth")
            
    except Exception as e:
        print(f"❌ Error en Auth: {e}")
    
    # Test 3: Verificar configuración de Auth
    print("\n3️⃣ Verificando configuración...")
    try:
        # Intentar obtener configuración
        settings = supabase_service.admin_client.auth.admin.get_settings()
        print(f"📋 Settings Auth: {settings}")
    except Exception as e:
        print(f"❌ Error obteniendo settings: {e}")

if __name__ == "__main__":
    asyncio.run(debug_registration())
