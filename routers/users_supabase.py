"""
Router de usuarios usando exclusivamente Supabase
Versión pura sin SQLAlchemy - Solo Supabase client nativo
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from services.supabase_service import supabase_service
from routers.auth_supabase import get_current_user

router = APIRouter()

# Pydantic models
class UserProfile(BaseModel):
    name: str
    avatar_url: Optional[str] = None
    mascot: Optional[str] = None

class SetupProfile(BaseModel):
    name: str
    avatar_url: str
    mascot: Optional[str] = None  # Solo para estudiantes

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    avatar_url: Optional[str] = None
    class_id: Optional[str] = None
    mascot: Optional[str] = None
    created_at: str

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile information"""
    try:
        # El usuario ya viene del get_current_user que usa Supabase
        return UserResponse(
            id=current_user["id"],
            email=current_user["email"],
            name=current_user.get("name", ""),
            role=current_user["role"],
            is_active=current_user.get("is_active", True),
            avatar_url=current_user.get("avatar_url"),
            class_id=current_user.get("class_id"),
            mascot=current_user.get("mascot"),
            created_at=current_user.get("created_at", "")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user profile: {str(e)}"
        )

@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_data: UserProfile,
    current_user: dict = Depends(get_current_user)
):
    """Update current user's profile"""
    try:
        # Preparar datos para actualizar
        update_data = {
            "name": profile_data.name
        }
        
        if profile_data.avatar_url:
            update_data["avatar_url"] = profile_data.avatar_url
            
        if profile_data.mascot and current_user["role"].upper() == "STUDENT":
            update_data["mascot"] = profile_data.mascot
        
        # Actualizar usuario en Supabase
        updated_user = await supabase_service.update_user(current_user["id"], update_data)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update user profile"
            )
        
        return UserResponse(
            id=updated_user["id"],
            email=updated_user["email"],
            name=updated_user["name"],
            role=updated_user["role"],
            is_active=updated_user.get("is_active", True),
            avatar_url=updated_user.get("avatar_url"),
            class_id=updated_user.get("class_id"),
            mascot=updated_user.get("mascot"),
            created_at=updated_user.get("created_at", "")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user profile: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    return await get_user_profile(current_user)

@router.post("/setup-profile", response_model=UserResponse)
async def setup_initial_profile(
    profile_data: SetupProfile,
    current_user: dict = Depends(get_current_user)
):
    """Configurar perfil inicial con avatar y mascota"""
    try:
        # Preparar datos para actualizar
        update_data = {
            "name": profile_data.name,
            "avatar_url": profile_data.avatar_url
        }
        
        # Solo estudiantes pueden tener mascota
        if current_user["role"].upper() == "STUDENT" and profile_data.mascot:
            update_data["mascot"] = profile_data.mascot
        
        # Actualizar usuario en Supabase
        updated_user = await supabase_service.update_user(current_user["id"], update_data)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to setup user profile"
            )
        
        return UserResponse(
            id=updated_user["id"],
            email=updated_user["email"],
            name=updated_user["name"],
            role=updated_user["role"],
            is_active=updated_user.get("is_active", True),
            avatar_url=updated_user.get("avatar_url"),
            class_id=updated_user.get("class_id"),
            mascot=updated_user.get("mascot"),
            created_at=updated_user.get("created_at", "")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting up user profile: {str(e)}"
        )

@router.get("/available-avatars")
async def get_available_avatars():
    """Obtener avatares disponibles"""
    return {
        "avatars": [
            {"id": "avatar1", "name": "Avatar 1", "url": "/avatars/avatar1.png"},
            {"id": "avatar2", "name": "Avatar 2", "url": "/avatars/avatar2.png"},
            {"id": "avatar3", "name": "Avatar 3", "url": "/avatars/avatar3.png"},
            {"id": "avatar4", "name": "Avatar 4", "url": "/avatars/avatar4.png"},
            {"id": "avatar5", "name": "Avatar 5", "url": "/avatars/avatar5.png"},
        ]
    }

@router.get("/available-mascots")
async def get_available_mascots():
    """Obtener mascotas disponibles (solo estudiantes)"""
    return {
        "mascots": [
            {"id": "carpi", "name": "Carpi", "url": "/mascotas/carpi.png"},
            {"id": "dino", "name": "Dino", "url": "/mascotas/dino.png"},
            {"id": "gato", "name": "Gato", "url": "/mascotas/gato.png"},
            {"id": "jabali", "name": "Jabalí", "url": "/mascotas/jabali.png"},
            {"id": "perro", "name": "Perro", "url": "/mascotas/perro.png"},
            {"id": "pollito", "name": "Pollito", "url": "/mascotas/pollito.png"},
        ]
    }

@router.delete("/profile")
async def delete_user_profile(current_user: dict = Depends(get_current_user)):
    """Delete current user's profile (soft delete)"""
    try:
        # Soft delete - marcar como inactivo
        update_data = {"is_active": False}
        updated_user = await supabase_service.update_user(current_user["id"], update_data)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete user profile"
            )
        
        return {"message": "User profile deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user profile: {str(e)}"
        )
