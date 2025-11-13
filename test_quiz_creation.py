"""
Script para diagnosticar usando la API directamente
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_direct_quiz_creation():
    """Probar crear quiz con diferentes enfoques"""
    print("🧪 Probando creación directa de quiz...")
    
    # Login
    login_data = {
        "email": "profesor@test.com",
        "password": "test123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code != 200:
            print("❌ Error en login")
            return
        
        auth_data = response.json()
        token = auth_data.get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Obtener clases
        response = requests.get(f"{BASE_URL}/classes/my-classes", headers=headers)
        if response.status_code != 200:
            print("❌ Error obteniendo clases")
            return
        
        classes = response.json()
        if not classes:
            print("❌ No hay clases")
            return
        
        class_id = classes[0]["id"]
        print(f"✅ Clase para pruebas: {classes[0]['name']} - ID: {class_id}")
        
        # Probar quiz sin campos problemáticos
        minimal_quiz_data = {
            "title": "Quiz Mínimo",
            "description": "Quiz de prueba sin enums",
            "class_id": class_id,
            "questions": [
                {
                    "question_text": "¿Cuánto es 1+1?",
                    "options": ["1", "2", "3", "4"],
                    "correct_answer": 1,
                    "explanation": "1+1=2",
                    "points": 10,
                    "time_limit": 30
                }
            ]
        }
        
        print("\n🧪 Probando quiz mínimo...")
        response = requests.post(f"{BASE_URL}/quizzes/", json=minimal_quiz_data, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201]:
            print("✅ ¡Quiz mínimo creado exitosamente!")
            quiz_data = response.json()
            quiz_id = quiz_data.get("id")
            
            # Verificar que se puede obtener
            get_response = requests.get(f"{BASE_URL}/quizzes/{quiz_id}", headers=headers)
            print(f"\n📋 Verificación - Status: {get_response.status_code}")
            if get_response.status_code == 200:
                quiz_detail = get_response.json()
                print(f"   Quiz: {quiz_detail.get('title')}")
                print(f"   Preguntas: {len(quiz_detail.get('questions', []))}")
                
        # Probar diferentes valores para difficulty usando valores que podrían existir
        possible_difficulties = [None, "beginner", "intermediate", "advanced", "basic", "normal", "expert"]
        
        print(f"\n🧪 Probando diferentes difficulties...")
        for difficulty in possible_difficulties:
            print(f"\n   Probando difficulty={difficulty}")
            
            test_quiz = {
                "title": f"Test Difficulty {difficulty}",
                "description": "Test",
                "class_id": class_id,
                "questions": [
                    {
                        "question_text": "Test?",
                        "options": ["A", "B"],
                        "correct_answer": 0,
                        "points": 10,
                        "time_limit": 30
                    }
                ]
            }
            
            if difficulty is not None:
                test_quiz["difficulty"] = difficulty
                test_quiz["questions"][0]["difficulty"] = difficulty
            
            response = requests.post(f"{BASE_URL}/quizzes/", json=test_quiz, headers=headers)
            print(f"      Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print(f"      ✅ FUNCIONA con difficulty='{difficulty}'")
                return difficulty
            else:
                error_msg = response.text
                if "invalid input value for enum" in error_msg:
                    # Extraer el valor del enum del error
                    start = error_msg.find("enum ") + 5
                    end = error_msg.find(":", start)
                    enum_name = error_msg[start:end] if end > start else "unknown"
                    print(f"      ❌ Enum '{enum_name}' no acepta '{difficulty}'")
                else:
                    print(f"      ❌ Otro error: {error_msg[:100]}...")
                    
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_quiz_creation()
