import os
from supabase import create_client
from dotenv import load_dotenv
load_dotenv()

try:
    client = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_KEY')
    )
    
    print("✅ Cliente creado exitosamente")
    
    # Test simple - listar tablas
    result = client.table('information_schema.tables').select('table_name').eq('table_schema', 'public').execute()
    print(f"📊 Tablas encontradas: {[t['table_name'] for t in result.data]}")
    
except Exception as e:
    print(f"❌ Error: {e}")
