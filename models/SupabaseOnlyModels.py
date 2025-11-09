# Ludix App Models - Supabase Only (No SQLAlchemy)
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# ENUMS
class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class AvatarType(str, Enum):
    POLLITO = "pollito"
    GATO = "gato"
    PERRO = "perro"
    DINO = "dino"
    JABALI = "jabali"
    CARPI = "carpi"

class GameType(str, Enum):
    QUIZ = "quiz"
    MATCHING = "matching"
    DRAG_DROP = "drag_drop"

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    OPEN_ENDED = "open_ended"

class SessionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

# PYDANTIC MODELS FOR SUPABASE

class UserBase(BaseModel):
    """Base User model"""
    email: str
    name: str
    role: UserRole
    status: UserStatus = UserStatus.ACTIVE
    avatar: Optional[AvatarType] = None
    preferences: Optional[Dict[str, Any]] = None

class UserCreate(UserBase):
    """User creation model"""
    password: str

class UserUpdate(BaseModel):
    """User update model"""
    name: Optional[str] = None
    avatar: Optional[AvatarType] = None
    status: Optional[UserStatus] = None
    preferences: Optional[Dict[str, Any]] = None

class User(UserBase):
    """User response model"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ClassroomBase(BaseModel):
    """Base Classroom model"""
    name: str
    description: Optional[str] = None
    teacher_id: str
    is_active: bool = True

class ClassroomCreate(ClassroomBase):
    """Classroom creation model"""
    pass

class Classroom(ClassroomBase):
    """Classroom response model"""
    id: str
    code: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class GameBase(BaseModel):
    """Base Game model"""
    title: str
    description: Optional[str] = None
    type: GameType
    classroom_id: str
    teacher_id: str
    config: Optional[Dict[str, Any]] = None
    is_active: bool = True

class GameCreate(GameBase):
    """Game creation model"""
    pass

class Game(GameBase):
    """Game response model"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    """Base Question model"""
    text: str
    type: QuestionType
    game_id: str
    options: Optional[List[str]] = None
    correct_answer: str
    points: int = 10
    order: int = 1

class QuestionCreate(QuestionBase):
    """Question creation model"""
    pass

class Question(QuestionBase):
    """Question response model"""
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

class GameSessionBase(BaseModel):
    """Base GameSession model"""
    game_id: str
    student_id: str
    status: SessionStatus = SessionStatus.PENDING

class GameSessionCreate(GameSessionBase):
    """GameSession creation model"""
    pass

class GameSession(GameSessionBase):
    """GameSession response model"""
    id: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    score: Optional[int] = None
    total_questions: int = 0
    correct_answers: int = 0
    time_spent: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AnswerBase(BaseModel):
    """Base Answer model"""
    session_id: str
    question_id: str
    answer_text: str
    is_correct: bool = False
    points_earned: int = 0

class AnswerCreate(AnswerBase):
    """Answer creation model"""
    pass

class Answer(AnswerBase):
    """Answer response model"""
    id: str
    answered_at: datetime

    class Config:
        from_attributes = True

# AUTH MODELS
class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    user: User

class LoginRequest(BaseModel):
    """Login request model"""
    email: str
    password: str

class RegisterRequest(BaseModel):
    """Register request model"""
    email: str
    password: str
    name: str
    role: UserRole
    mascot: Optional[AvatarType] = None

# API RESPONSE MODELS
class APIResponse(BaseModel):
    """Generic API response"""
    success: bool
    message: str
    data: Optional[Any] = None

class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    service: str = "Ludix API"

# MASCOT INFO
AVAILABLE_MASCOTS = [
    {"id": "pollito", "name": "Pollito", "description": "Un pollito amarillo muy tierno"},
    {"id": "gato", "name": "Gato", "description": "Un gato naranja muy juguetón"},
    {"id": "perro", "name": "Perro", "description": "Un perro fiel y amigable"},
    {"id": "dino", "name": "Dino", "description": "Un dinosaurio verde muy aventurero"},
    {"id": "jabali", "name": "Jabalí", "description": "Un jabalí valiente y fuerte"},
    {"id": "carpi", "name": "Carpi", "description": "Un carpincho relajado y sabio"},
]
