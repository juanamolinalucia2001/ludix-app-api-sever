from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base
import enum
from datetime import datetime

class UserRole(enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"

class User(Base):
    """
    User model for both teachers and students.
    Factory Pattern: Different user types created based on role.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Nullable for Google auth
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Google auth fields
    google_id = Column(String(255), unique=True, nullable=True)
    
    # Student specific fields
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    mascot = Column(String(50), nullable=True)  # dragon, unicorn, robot, cat, dog
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    classes_owned = relationship("Class", back_populates="teacher", foreign_keys="Class.teacher_id")
    enrolled_class = relationship("Class", back_populates="students", foreign_keys=[class_id])
    
    # Game sessions (for students)
    game_sessions = relationship("GameSession", back_populates="student")
    
    # Created content (for teachers)
    created_quizzes = relationship("Quiz", back_populates="creator")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"

    @property
    def is_teacher(self) -> bool:
        return self.role == UserRole.TEACHER

    @property
    def is_student(self) -> bool:
        return self.role == UserRole.STUDENT

    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role.value,
            "is_active": self.is_active,
            "avatar_url": self.avatar_url,
            "class_id": self.class_id,
            "mascot": self.mascot,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
