"""
Script para diagnosticar los enums de Supabase
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_enum_values():
    """Probar diferentes valores de enums"""
    print("🔍 Diagnosticando enums de Supabase...")
    
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
        print(f"✅ Clase para pruebas: {classes[0]['name']}")
        
        # Probar diferentes valores de difficulty
        difficulty_values = ["easy", "EASY", "medium", "MEDIUM", "hard", "HARD"]
        question_types = ["multiple_choice", "MULTIPLE_CHOICE", "true_false", "TRUE_FALSE", "text", "TEXT"]
        
        print("\n🧪 Probando valores de difficulty...")
        for difficulty in difficulty_values:
            print(f"\n   Probando difficulty='{difficulty}'")
            
            quiz_data = {
                "title": f"Test Quiz - {difficulty}",
                "description": "Quiz de prueba para diagnosticar enums",
                "class_id": class_id,
                "time_limit": 300,
                "difficulty": difficulty,
                "topic": "Test",
                "questions": [
                    {
                        "question_text": "¿Pregunta de prueba?",
                        "question_type": "multiple_choice",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": 0,
                        "explanation": "Respuesta de prueba",
                        "difficulty": difficulty,
                        "points": 10,
                        "time_limit": 30
                    }
                ]
            }
            
            try:
                response = requests.post(f"{BASE_URL}/quizzes/", json=quiz_data, headers=headers)
                print(f"      Status: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    print(f"      ✅ FUNCIONA - Quiz ID: {result.get('id')}")
                    return difficulty  # Retornar el primer valor que funcione
                else:
                    error_text = response.text
                    print(f"      ❌ Error: {error_text}")
                    
            except Exception as e:
                print(f"      ❌ Excepción: {e}")
        
        print("\n🧪 Probando valores de question_type...")
        for qtype in question_types:
            print(f"\n   Probando question_type='{qtype}'")
            
            quiz_data = {
                "title": f"Test Quiz - {qtype}",
                "description": "Quiz de prueba para diagnosticar enums",
                "class_id": class_id,
                "time_limit": 300,
                "difficulty": "medium",  # Usar un valor que sabemos que no funciona aún
                "topic": "Test",
                "questions": [
                    {
                        "question_text": "¿Pregunta de prueba?",
                        "question_type": qtype,
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": 0,
                        "explanation": "Respuesta de prueba",
                        "difficulty": "medium",
                        "points": 10,
                        "time_limit": 30
                    }
                ]
            }
            
            try:
                response = requests.post(f"{BASE_URL}/quizzes/", json=quiz_data, headers=headers)
                print(f"      Status: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    print(f"      ✅ FUNCIONA - Question type válido")
                else:
                    error_text = response.text
                    print(f"      ❌ Error: {error_text}")
                    
            except Exception as e:
                print(f"      ❌ Excepción: {e}")
                
    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    test_enum_values()
