"""
Script para crear un usuario de prueba para los tests
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def create_test_user():
    """Crear usuario de prueba"""
    print("👤 Creando usuario de prueba...")
    
    # Datos del usuario de prueba
    user_data = {
        "email": "profesor@test.com",
        "password": "test123",
        "name": "Profesor Test",
        "role": "teacher"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Usuario creado exitosamente!")
            print(f"   ID: {result.get('user', {}).get('id')}")
            print(f"   Nombre: {result.get('user', {}).get('name')}")
            print(f"   Email: {result.get('user', {}).get('email')}")
            print(f"   Rol: {result.get('user', {}).get('role')}")
            return result.get('user')
        elif response.status_code == 200:
            # El usuario ya existe y se logeó automáticamente
            result = response.json()
            print("✅ Usuario ya existe (auto-login exitoso)!")
            user_info = result.get('user', {})
            print(f"   ID: {user_info.get('id')}")
            print(f"   Nombre: {user_info.get('name')}")
            print(f"   Email: {user_info.get('email')}")
            print(f"   Rol: {user_info.get('role')}")
            return user_info
        else:
            print(f"❌ Error creando usuario: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def create_test_class(token):
    """Crear una clase de prueba"""
    print("\n🏫 Creando clase de prueba...")
    
    headers = {"Authorization": f"Bearer {token}"}
    class_data = {
        "name": "Matemáticas 5to Grado",
        "description": "Clase de matemáticas para estudiantes de 5to grado",
        "max_students": 30
    }
    
    try:
        response = requests.post(f"{BASE_URL}/classes", json=class_data, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Clase creada exitosamente!")
            print(f"   Nombre: {result.get('name')}")
            print(f"   Código: {result.get('class_code')}")
            return result
        else:
            print(f"❌ Error creando clase: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    print("🚀 Configurando datos iniciales para testing...")
    
    # 1. Crear usuario de prueba
    user = create_test_user()
    if not user:
        print("❌ No se pudo crear el usuario. Abortando.")
        return
    
    # 2. Hacer login para obtener token
    print("\n🔐 Haciendo login...")
    login_data = {
        "email": "profesor@test.com",
        "password": "test123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            auth_data = response.json()
            token = auth_data.get("access_token")
            print("✅ Login exitoso!")
        else:
            print(f"❌ Error en login: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error en login: {e}")
        return
    
    # 3. Crear clase de prueba
    class_obj = create_test_class(token)
    
    print("\n" + "="*50)
    print("✅ Configuración inicial completada!")
    print("👤 Usuario: profesor@test.com / test123")
    if class_obj:
        print(f"🏫 Clase: {class_obj.get('name')} (Código: {class_obj.get('class_code')})")
    print("🧪 Ahora puedes ejecutar test_api.py")

if __name__ == "__main__":
    main()
