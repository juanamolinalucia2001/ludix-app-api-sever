"""
Script para consultar los valores de enums directamente desde Supabase
"""

from services.supabase_service import supabase_service

def query_enum_values():
    """Consultar los valores de enums desde Supabase"""
    print("🔍 Consultando valores de enums en Supabase...")
    
    try:
        # Query para obtener los valores de los enums
        queries = [
            """
            SELECT 
                t.typname AS enum_name,
                e.enumlabel AS enum_value
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid  
            WHERE t.typname IN ('difficultylevel', 'questiontype', 'userrole', 'sessionstatus')
            ORDER BY t.typname, e.enumsortorder;
            """,
            
            # Query alternativo si el primero no funciona
            """
            SELECT DISTINCT 
                difficulty 
            FROM quizzes 
            WHERE difficulty IS NOT NULL
            LIMIT 10;
            """,
            
            # Otro query para role
            """
            SELECT DISTINCT 
                role 
            FROM users 
            WHERE role IS NOT NULL
            LIMIT 10;
            """
        ]
        
        for i, query in enumerate(queries):
            print(f"\n📋 Ejecutando consulta {i+1}...")
            try:
                result = supabase_service.client.rpc('query_enums', {'query_text': query}).execute()
                print(f"   Resultado: {result}")
            except Exception as e:
                print(f"   ❌ Error en consulta {i+1}: {e}")
                
                # Intentar consulta directa
                try:
                    if i == 1:  # Query de difficulty
                        result = supabase_service.client.table("quizzes").select("difficulty").limit(10).execute()
                        print(f"   Difficulty values: {[r.get('difficulty') for r in result.data if r.get('difficulty')]}")
                except Exception as e2:
                    print(f"   ❌ Error en consulta directa: {e2}")
                    
                try:
                    if i == 2:  # Query de role
                        result = supabase_service.client.table("users").select("role").limit(10).execute()
                        print(f"   Role values: {set(r.get('role') for r in result.data if r.get('role'))}")
                except Exception as e2:
                    print(f"   ❌ Error en consulta directa: {e2}")
    
    except Exception as e:
        print(f"❌ Error general: {e}")

def test_simple_quiz_creation():
    """Probar crear un quiz sin enums complicados"""
    print("\n🧪 Probando creación simple de quiz...")
    
    try:
        # Obtener una clase existente
        classes_result = supabase_service.client.table("classes").select("*").limit(1).execute()
        if not classes_result.data:
            print("❌ No hay clases disponibles")
            return
        
        class_id = classes_result.data[0]["id"]
        creator_id = classes_result.data[0]["teacher_id"]
        
        print(f"✅ Usando clase: {class_id}")
        print(f"✅ Creador: {creator_id}")
        
        # Intentar insertar directamente en quizzes sin difficulty
        quiz_data = {
            "id": "test-quiz-123",
            "title": "Quiz de Prueba Simple",
            "description": "Test",
            "creator_id": creator_id,
            "class_id": class_id,
            "time_limit": 300,
            "is_active": True,
            "is_published": False,
            "topic": "Test"
            # NO incluir difficulty, question_type, etc.
        }
        
        result = supabase_service.client.table("quizzes").insert(quiz_data).execute()
        
        if result.data:
            print("✅ Quiz simple creado exitosamente!")
            quiz_id = result.data[0]["id"]
            
            # Ahora intentar crear una pregunta simple
            question_data = {
                "id": "test-question-123",
                "quiz_id": quiz_id,
                "question_text": "¿Pregunta de prueba?",
                "options": ["A", "B", "C", "D"],
                "correct_answer": 0,
                "points": 10,
                "time_limit": 30,
                "order_index": 0
                # NO incluir question_type, difficulty
            }
            
            question_result = supabase_service.client.table("questions").insert(question_data).execute()
            
            if question_result.data:
                print("✅ Pregunta simple creada exitosamente!")
                
                # Verificar que se guardó
                verify_quiz = supabase_service.client.table("quizzes").select("*").eq("id", quiz_id).execute()
                print(f"📋 Quiz verificado: {verify_quiz.data[0] if verify_quiz.data else 'No encontrado'}")
                
                verify_question = supabase_service.client.table("questions").select("*").eq("id", "test-question-123").execute()
                print(f"📋 Pregunta verificada: {verify_question.data[0] if verify_question.data else 'No encontrada'}")
                
            else:
                print(f"❌ Error creando pregunta: {question_result}")
        else:
            print(f"❌ Error creando quiz: {result}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    query_enum_values()
    test_simple_quiz_creation()
