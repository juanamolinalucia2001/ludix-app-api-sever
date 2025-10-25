from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from database.connection import get_db
from services.AuthService import auth_service, security
from models.User import User, UserRole
from pydantic import BaseModel, EmailStr

router = APIRouter()

# Pydantic models for request/response
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str  # "teacher" or "student"

class GoogleAuth(BaseModel):
    google_token: str
    role: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

class RefreshToken(BaseModel):
    refresh_token: str

@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user with email and password.
    Returns JWT tokens and user information.
    """
    # Authenticate user
    user = auth_service.authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create tokens
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
    access_token = auth_service.create_access_token(token_data)
    refresh_token = auth_service.create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=auth_service.access_token_expire_minutes * 60,
        user=user.to_dict()
    )

@router.post("/register", response_model=TokenResponse)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate role
    if user_data.role not in ["teacher", "student"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'teacher' or 'student'"
        )
    
    # Create new user
    hashed_password = auth_service.hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
        role=UserRole.TEACHER if user_data.role == "teacher" else UserRole.STUDENT,
        last_login=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create tokens
    token_data = {"sub": str(new_user.id), "email": new_user.email, "role": new_user.role.value}
    access_token = auth_service.create_access_token(token_data)
    refresh_token = auth_service.create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=auth_service.access_token_expire_minutes * 60,
        user=new_user.to_dict()
    )

@router.post("/google", response_model=TokenResponse)
async def google_login(
    auth_data: GoogleAuth,
    db: Session = Depends(get_db)
):
    """
    Authenticate user with Google OAuth token.
    """
    # TODO: Implement Google token verification
    # For now, we'll return a placeholder response
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google authentication will be implemented in the next iteration"
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    token_data: RefreshToken,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    # Verify refresh token
    payload = auth_service.verify_token(token_data.refresh_token, "refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
    access_token = auth_service.create_access_token(token_data)
    new_refresh_token = auth_service.create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=auth_service.access_token_expire_minutes * 60,
        user=user.to_dict()
    )

@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Logout user (invalidate token on client side).
    """
    # In a production environment, you might want to maintain a blacklist of tokens
    # For now, we'll just return success (client should remove the token)
    return {"message": "Successfully logged out"}

@router.get("/me")
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information.
    """
    user = auth_service.get_user_from_token(db, credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user.to_dict()
