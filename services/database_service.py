"""
Servicio híbrido para usar Supabase con fallback a SQLAlchemy
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from core.config import settings

# Intentar importar Supabase, si no está disponible usar solo SQLAlchemy
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

class DatabaseService:
    """Servicio de base de datos que puede usar Supabase o SQLAlchemy"""
    
    def __init__(self):
        self.supabase_client: Optional[Client] = None
        self.use_supabase = False
        
        # Intentar conectar a Supabase si está configurado
        if (SUPABASE_AVAILABLE and 
            settings.SUPABASE_URL and 
            settings.SUPABASE_KEY):
            try:
                self.supabase_client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_KEY
                )
                self.use_supabase = True
                print("✅ Using Supabase as database")
            except Exception as e:
                print(f"⚠️  Supabase connection failed: {e}")
                print("🔄 Falling back to SQLAlchemy")
                self.use_supabase = False
        else:
            print("📊 Using SQLAlchemy (local database)")
    
    def get_client(self) -> Optional[Client]:
        """Get Supabase client if available"""
        return self.supabase_client if self.use_supabase else None
    
    def is_using_supabase(self) -> bool:
        """Check if using Supabase"""
        return self.use_supabase
    
    async def create_user(self, email: str, password: str, full_name: str, role: str = "student") -> Dict[str, Any]:
        """Create user in Supabase or return data for SQLAlchemy"""
        if self.use_supabase:
            try:
                # Crear usuario en Supabase Auth
                auth_response = self.supabase_client.auth.sign_up({
                    "email": email,
                    "password": password
                })
                
                if auth_response.user:
                    # Crear perfil en tabla users
                    profile_response = self.supabase_client.table("users").insert({
                        "id": auth_response.user.id,
                        "email": email,
                        "full_name": full_name,
                        "role": role
                    }).execute()
                    
                    return {
                        "success": True,
                        "user_id": auth_response.user.id,
                        "email": email,
                        "data": profile_response.data
                    }
                else:
                    return {"success": False, "error": "Failed to create user"}
                    
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            # Retornar datos para que SQLAlchemy los maneje
            return {
                "success": False, 
                "fallback_to_sqlalchemy": True,
                "user_data": {
                    "email": email,
                    "full_name": full_name,
                    "role": role
                }
            }
    
    async def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user with Supabase or return data for SQLAlchemy"""
        if self.use_supabase:
            try:
                auth_response = self.supabase_client.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                if auth_response.user:
                    # Obtener perfil del usuario
                    profile_response = self.supabase_client.table("users").select("*").eq("id", auth_response.user.id).execute()
                    
                    return {
                        "success": True,
                        "user": auth_response.user,
                        "profile": profile_response.data[0] if profile_response.data else None,
                        "session": auth_response.session
                    }
                else:
                    return {"success": False, "error": "Invalid credentials"}
                    
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            return {
                "success": False,
                "fallback_to_sqlalchemy": True,
                "credentials": {"email": email, "password": password}
            }

# Instancia global del servicio
db_service = DatabaseService()

def get_database_service() -> DatabaseService:
    """Dependency para obtener el servicio de base de datos"""
    return db_service
