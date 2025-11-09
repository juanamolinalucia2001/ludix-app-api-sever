import os
from supabase import create_client, Client

# Cargar variables del .env
from dotenv import load_dotenv
load_dotenv()

print("🔍 Testing Supabase Connection...")
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
print(f"SUPABASE_KEY length: {len(os.getenv('SUPABASE_KEY', ''))}")
print(f"SUPABASE_SERVICE_KEY length: {len(os.getenv('SUPABASE_SERVICE_KEY', ''))}")

try:
    # Test con anon key
    print("\n🔹 Testing with ANON key...")
    anon_client = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )
    
    # Test simple query
    result = anon_client.table('users').select('id').limit(1).execute()
    print(f"✅ ANON client works: {len(result.data)} records")
    
except Exception as e:
    print(f"❌ ANON client error: {e}")

try:
    # Test con service key
    print("\n🔹 Testing with SERVICE key...")
    service_client = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_KEY')
    )
    
    # Test simple query
    result = service_client.table('users').select('id').limit(1).execute()
    print(f"✅ SERVICE client works: {len(result.data)} records")
    
except Exception as e:
    print(f"❌ SERVICE client error: {e}")

# Test auth
try:
    print("\n🔹 Testing Auth...")
    auth_test = service_client.auth.admin.list_users()
    print(f"✅ Auth works: {len(auth_test.users)} users")
    
except Exception as e:
    print(f"❌ Auth error: {e}")
