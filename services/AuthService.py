from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from jose import JWTError, jwt
import hashlib
import secrets
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from core.config import settings
from database.connection import get_db
from models.User import User

security = HTTPBearer()

class AuthService:
    """
    Authentication service implementing Decorator Pattern for token management.
    Singleton Pattern: Single instance for all auth operations.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuthService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    # Password operations
    def hash_password(self, password: str) -> str:
        """Hash a password using SHA256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            salt, password_hash = hashed_password.split(':')
            return hashlib.sha256((plain_password + salt).encode()).hexdigest() == password_hash
        except ValueError:
            return False

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not user.hashed_password:  # Google-only user
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    # Token operations
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != token_type:
                return None
            return payload
        except JWTError:
            return None

    def get_user_from_token(self, db: Session, token: str) -> Optional[User]:
        """Get user from JWT token"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
            
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user

    # Decorator Pattern: Token validation decorator
    def require_auth(self, require_role: Optional[str] = None):
        """
        Decorator for endpoints requiring authentication.
        Optionally requires specific role.
        """
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Extract dependencies
                credentials = kwargs.get('credentials')
                db = kwargs.get('db')
                
                if not credentials or not db:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                user = self.get_user_from_token(db, credentials.credentials)
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
                
                if require_role and user.role.value != require_role:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Role '{require_role}' required"
                    )
                
                # Add user to kwargs
                kwargs['current_user'] = user
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator

# Singleton instance
auth_service = AuthService()

# Dependency functions for FastAPI
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """FastAPI dependency to get current authenticated user"""
    user = auth_service.get_user_from_token(db, credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    return user

async def get_current_teacher(
    current_user: User = Depends(get_current_user)
) -> User:
    """FastAPI dependency to get current teacher user"""
    if not current_user.is_teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher role required"
        )
    return current_user

async def get_current_student(
    current_user: User = Depends(get_current_user)
) -> User:
    """FastAPI dependency to get current student user"""
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student role required"
        )
    return current_user

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """FastAPI dependency to get current user (optional)"""
    if not credentials:
        return None
    return auth_service.get_user_from_token(db, credentials.credentials)
