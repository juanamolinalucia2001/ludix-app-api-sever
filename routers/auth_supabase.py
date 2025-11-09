"""
Router de autenticación usando exclusivamente Supabase
Sin SQLAlchemy - Solo Supabase client nativo
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional
import jwt
from datetime import datetime, timedelta

from services.supabase_service import supabase_service
from core.config import settings

router = APIRouter()
security = HTTPBearer()

# Pydantic models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "student"  # "teacher" or "student"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

class RefreshToken(BaseModel):
    refresh_token: str

# Helper functions
def create_access_token(data: dict) -> str:
    """Crear JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Crear JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_token(token: str) -> Optional[dict]:
    """Verificar JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtener usuario actual desde token"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = await supabase_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

# Endpoints
@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    """Registrar nuevo usuario"""
    try:
        # Verificar si el usuario ya existe
        existing_user = await supabase_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Validar rol
        if user_data.role not in ["teacher", "student"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role must be 'teacher' or 'student'"
            )
        
        # Crear usuario
        user = await supabase_service.create_user(
            email=user_data.email,
            password=user_data.password,
            name=user_data.name,
            role=user_data.role
        )
        
        # Crear tokens
        token_data = {
            "sub": user["id"],
            "email": user["email"],
            "role": user["role"]
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Iniciar sesión"""
    try:
        # Autenticar usuario
        auth_result = await supabase_service.authenticate_user(
            user_data.email, 
            user_data.password
        )
        
        if not auth_result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Crear tokens personalizados (opcional: usar los de Supabase)
        token_data = {
            "sub": auth_result["id"],
            "email": auth_result["email"],
            "role": auth_result["role"]
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        user_info = {
            "id": auth_result["id"],
            "email": auth_result["email"],
            "name": auth_result["name"],
            "role": auth_result["role"],
            "is_active": auth_result["is_active"]
        }
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(token_data: RefreshToken):
    """Renovar access token"""
    try:
        payload = verify_token(token_data.refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload.get("sub")
        user = await supabase_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Crear nuevos tokens
        new_token_data = {
            "sub": user["id"],
            "email": user["email"],
            "role": user["role"]
        }
        
        access_token = create_access_token(new_token_data)
        new_refresh_token = create_refresh_token(new_token_data)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Obtener información del usuario actual"""
    return current_user

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Cerrar sesión (simbólico - los JWT no se pueden invalidar sin blacklist)"""
    return {"message": "Successfully logged out"}

@router.post("/google")
async def google_login():
    """Google OAuth (no implementado aún)"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google authentication will be implemented with Supabase Auth"
    )
