"""
Script para crear estudiantes de prueba
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def create_test_students():
    """Crear estudiantes de prueba"""
    print("👨‍🎓 Creando estudiantes de prueba...")
    
    students_data = [
        {
            "email": "alumno1@test.com",
            "password": "test123",
            "name": "María García",
            "role": "student"
        },
        {
            "email": "alumno2@test.com", 
            "password": "test123",
            "name": "Juan Pérez",
            "role": "student"
        },
        {
            "email": "alumno3@test.com",
            "password": "test123", 
            "name": "Ana López",
            "role": "student"
        },
        {
            "email": "alumno4@test.com",
            "password": "test123",
            "name": "Carlos Rodríguez",
            "role": "student"
        },
        {
            "email": "alumno5@test.com",
            "password": "test123",
            "name": "Sofia Martínez",
            "role": "student"
        }
    ]
    
    created_students = []
    
    for student_data in students_data:
        try:
            response = requests.post(f"{BASE_URL}/auth/register", json=student_data)
            print(f"   {student_data['name']}: Status {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                user_info = result.get('user', result)
                print(f"      ✅ Creado - ID: {user_info.get('id')}")
                created_students.append(user_info)
            elif response.status_code == 400 and "already registered" in response.text:
                print(f"      ✅ Ya existe")
            else:
                print(f"      ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error creando {student_data['name']}: {e}")
    
    return created_students

def join_students_to_class():
    """Hacer que los estudiantes se unan a la clase"""
    print("\n🏫 Uniendo estudiantes a la clase...")
    
    # Primero obtener el código de clase del profesor
    login_data = {
        "email": "profesor@test.com",
        "password": "test123"
    }
    
    try:
        # Login del profesor
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code != 200:
            print("   ❌ Error haciendo login del profesor")
            return
        
        auth_data = response.json()
        teacher_token = auth_data.get("access_token")
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        # Obtener clases del profesor
        response = requests.get(f"{BASE_URL}/classes/my-classes", headers=headers)
        if response.status_code != 200:
            print("   ❌ Error obteniendo clases del profesor")
            return
        
        classes = response.json()
        if not classes:
            print("   ❌ No hay clases disponibles")
            return
        
        class_code = classes[0]["class_code"]
        print(f"   📋 Código de clase: {class_code}")
        
        # Estudiantes para unir
        students_credentials = [
            {"email": "alumno1@test.com", "password": "test123", "name": "María García"},
            {"email": "alumno2@test.com", "password": "test123", "name": "Juan Pérez"},
            {"email": "alumno3@test.com", "password": "test123", "name": "Ana López"},
        ]
        
        for student_cred in students_credentials:
            try:
                # Login del estudiante
                student_login = {
                    "email": student_cred["email"],
                    "password": student_cred["password"]
                }
                
                response = requests.post(f"{BASE_URL}/auth/login", json=student_login)
                if response.status_code != 200:
                    print(f"      ❌ Error login {student_cred['name']}")
                    continue
                
                student_auth = response.json()
                student_token = student_auth.get("access_token")
                student_headers = {"Authorization": f"Bearer {student_token}"}
                
                # Unirse a la clase
                join_data = {"class_code": class_code}
                response = requests.post(f"{BASE_URL}/classes/join", json=join_data, headers=student_headers)
                
                print(f"   {student_cred['name']}: Status {response.status_code}")
                if response.status_code in [200, 201]:
                    print(f"      ✅ Unido a la clase exitosamente")
                else:
                    print(f"      ⚠️ Respuesta: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Error uniendo {student_cred['name']}: {e}")
        
    except Exception as e:
        print(f"   ❌ Error general: {e}")

def main():
    print("🚀 Creando ecosystem de prueba completo...")
    
    # 1. Crear estudiantes
    students = create_test_students()
    
    # 2. Unir estudiantes a clase
    join_students_to_class()
    
    print("\n" + "="*50)
    print("✅ Ecosystem de prueba creado!")
    print("👨‍🏫 Profesor: profesor@test.com / test123")
    print("👨‍🎓 Estudiantes: alumno1@test.com, alumno2@test.com, etc. / test123")
    print("🧪 Ahora ejecuta test_api.py para poblar con quizzes")

if __name__ == "__main__":
    main()
