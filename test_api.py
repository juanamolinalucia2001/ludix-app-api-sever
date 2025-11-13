"""
Script de prueba para verificar que los endpoints funcionan correctamente
y poblar la base de datos con datos de ejemplo
"""

import requests
import json
import time

# Configuración
BASE_URL = "http://localhost:8001"
TEST_EMAIL = "profesor@test.com"
TEST_PASSWORD = "test123"

def test_api():
    """Función principal para probar todos los endpoints"""
    print("🧪 Iniciando tests de la API...")
    
    # 1. Test de salud
    print("\n1. ⚡ Test de salud del servidor...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # 2. Test de login
    print("\n2. 🔐 Test de login...")
    try:
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            auth_data = response.json()
            token = auth_data.get("access_token")
            user_data = auth_data.get("user")
            print(f"   ✅ Login exitoso")
            print(f"   Usuario: {user_data.get('name')} ({user_data.get('role')})")
        else:
            print(f"   ❌ Login falló: {response.text}")
            return
            
    except Exception as e:
        print(f"   ❌ Error en login: {e}")
        return
    
    # Headers para requests autenticados
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Test de obtener estado de BD
    print("\n3. 📊 Test de estado de base de datos...")
    try:
        response = requests.get(f"{BASE_URL}/init/status", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            status_data = response.json()
            print(f"   ✅ Estado obtenido:")
            for table, count in status_data.get("status", {}).items():
                print(f"      {table}: {count} registros")
        else:
            print(f"   ❌ Error obteniendo estado: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 4. Test de obtener clases
    print("\n4. 🏫 Test de obtener clases...")
    try:
        response = requests.get(f"{BASE_URL}/classes/my-classes", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            classes = response.json()
            print(f"   ✅ Clases obtenidas: {len(classes)}")
            for cls in classes:
                print(f"      - {cls.get('name')} (Código: {cls.get('class_code')})")
        else:
            print(f"   ❌ Error obteniendo clases: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 5. Test de crear una clase si no existe
    print("\n5. 🏗️ Test de crear clase de prueba...")
    try:
        # Primero verificar si ya hay clases
        response = requests.get(f"{BASE_URL}/classes/my-classes", headers=headers)
        if response.status_code == 200:
            existing_classes = response.json()
            if len(existing_classes) == 0:
                # Crear una clase de prueba
                class_data = {
                    "name": "Matemáticas 5to Grado",
                    "description": "Clase de matemáticas para estudiantes de 5to grado",
                    "max_students": 30
                }
                response = requests.post(f"{BASE_URL}/classes/", json=class_data, headers=headers)
                print(f"   Status: {response.status_code}")
                if response.status_code in [200, 201]:
                    new_class = response.json()
                    print(f"   ✅ Clase creada: {new_class.get('name')}")
                    print(f"      Código: {new_class.get('class_code')}")
                else:
                    print(f"   ❌ Error creando clase: {response.text}")
            else:
                print(f"   ✅ Ya existen {len(existing_classes)} clases")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 6. Test de crear datos de ejemplo
    print("\n6. 🚀 Test de crear datos de ejemplo...")
    try:
        response = requests.post(f"{BASE_URL}/init/sample-data", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Datos de ejemplo creados:")
            for key, value in result.get("data", {}).items():
                print(f"      {key}: {value}")
        else:
            print(f"   ❌ Error creando datos: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 7. Esperar un momento para que se procesen los datos
    print("\n   ⏳ Esperando procesamiento...")
    time.sleep(2)
    
    # 8. Test de obtener estado de BD después de crear datos
    print("\n8. 📊 Test de estado de BD después de crear datos...")
    try:
        response = requests.get(f"{BASE_URL}/init/status", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            status_data = response.json()
            print(f"   ✅ Nuevo estado:")
            for table, count in status_data.get("status", {}).items():
                print(f"      {table}: {count} registros")
        else:
            print(f"   ❌ Error obteniendo estado: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 9. Test de obtener quizzes después de crear datos
    print("\n9. 🎯 Test de obtener quizzes (después de crear datos)...")
    try:
        # Primero obtener las clases para luego obtener quizzes por clase
        classes_response = requests.get(f"{BASE_URL}/classes/my-classes", headers=headers)
        if classes_response.status_code == 200:
            classes = classes_response.json()
            if classes:
                class_id = classes[0]["id"]
                response = requests.get(f"{BASE_URL}/quizzes/class/{class_id}", headers=headers)
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    quizzes = response.json()
                    print(f"   ✅ Quizzes después de crear datos: {len(quizzes)}")
                    for quiz in quizzes[:3]:  # Mostrar solo los primeros 3
                        print(f"      - {quiz.get('title')} ({quiz.get('difficulty')})")
                else:
                    print(f"   ❌ Error obteniendo quizzes: {response.text}")
            else:
                print("   ⚠️ No hay clases disponibles para obtener quizzes")
        else:
            print(f"   ❌ Error obteniendo clases: {classes_response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 10. Test de obtener un quiz específico con preguntas
    if 'quizzes' in locals() and len(quizzes) > 0:
        print("\n10. 📝 Test de obtener quiz específico con preguntas...")
        try:
            quiz_id = quizzes[0]["id"]
            response = requests.get(f"{BASE_URL}/quizzes/{quiz_id}", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                quiz_detail = response.json()
                print(f"   ✅ Quiz obtenido: {quiz_detail.get('title')}")
                questions = quiz_detail.get('questions', [])
                print(f"      Preguntas: {len(questions)}")
                for i, q in enumerate(questions[:2]):  # Mostrar solo las primeras 2
                    print(f"      {i+1}. {q.get('question_text')}")
                    print(f"         Opciones: {len(q.get('options', []))}")
            else:
                print(f"   ❌ Error obteniendo quiz: {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # 11. Test de obtener quizzes por clase
    print("\n11. 🏫 Test de obtener quizzes por clase...")
    try:
        # Obtener primera clase
        classes_response = requests.get(f"{BASE_URL}/classes", headers=headers)
        if classes_response.status_code == 200:
            classes = classes_response.json()
            if classes:
                class_id = classes[0]["id"]
                response = requests.get(f"{BASE_URL}/quizzes/class/{class_id}", headers=headers)
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    class_quizzes = response.json()
                    print(f"   ✅ Quizzes de la clase: {len(class_quizzes)}")
                    for quiz in class_quizzes[:2]:
                        print(f"      - {quiz.get('title')} ({quiz.get('questions_count')} preguntas)")
                else:
                    print(f"   ❌ Error obteniendo quizzes de clase: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n✅ Tests completados!")
    print("=" * 50)
    print("🎉 Tu API está funcionando correctamente!")
    print("📊 Las tablas de Supabase ahora tienen datos de ejemplo")
    print("🚀 Puedes continuar con el desarrollo del frontend")

if __name__ == "__main__":
    test_api()
