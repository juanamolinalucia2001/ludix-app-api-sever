from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base
import enum
import uuid
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from typing import List, Dict, Any

class DifficultyLevel(enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class QuestionType(enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"

class Class(Base):
    """Class/Classroom model for organizing students and content"""
    __tablename__ = "classes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    class_code = Column(String(10), unique=True, nullable=False)  # For student enrollment
    is_active = Column(Boolean, default=True)
    
    # Settings
    max_students = Column(Integer, default=50)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    teacher = relationship("User", back_populates="classes_owned", foreign_keys=[teacher_id])
    students = relationship("User", back_populates="enrolled_class", foreign_keys="User.class_id")
    quizzes = relationship("Quiz", back_populates="class_obj")

    def __repr__(self):
        return f"<Class(id={self.id}, name='{self.name}', teacher_id={self.teacher_id})>"

class Quiz(Base):
    """
    Quiz model for game content.
    Factory Pattern: Different quiz types can be created.
    """
    __tablename__ = "quizzes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    
    # Quiz settings
    time_limit = Column(Integer, nullable=True)  # In seconds
    difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.EASY)
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)
    
    # Ordering and categorization
    topic = Column(String(255), nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tags
    order_index = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    creator = relationship("User", back_populates="created_quizzes")
    class_obj = relationship("Class", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    game_sessions = relationship("GameSession", back_populates="quiz")

    def __repr__(self):
        return f"<Quiz(id={self.id}, title='{self.title}', creator_id={self.creator_id})>"

    @property
    def total_questions(self) -> int:
        return len(self.questions)

    def to_dict(self, include_questions: bool = False):
        """Convert quiz to dictionary for API responses"""
        data = {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "creator_id": str(self.creator_id),
            "class_id": str(self.class_id),
            "time_limit": self.time_limit,
            "difficulty": self.difficulty.value,
            "is_active": self.is_active,
            "is_published": self.is_published,
            "topic": self.topic,
            "tags": self.tags or [],
            "order_index": self.order_index,
            "total_questions": self.total_questions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None
        }
        
        if include_questions:
            data["questions"] = [q.to_dict() for q in self.questions]
            
        return data

class Question(Base):
    """
    Question model for quiz content.
    Factory Pattern: Different question types.
    """
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(Enum(QuestionType), default=QuestionType.MULTIPLE_CHOICE)
    
    # Multiple choice options
    options = Column(JSON, nullable=True)  # Array of options
    correct_answer = Column(Integer, nullable=False)  # Index of correct option
    
    # Additional content
    explanation = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    audio_url = Column(String(500), nullable=True)
    
    # Question settings
    difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.EASY)
    points = Column(Integer, default=1)
    time_limit = Column(Integer, nullable=True)  # In seconds, overrides quiz time
    order_index = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    answers = relationship("Answer", back_populates="question")

    def __repr__(self):
        return f"<Question(id={self.id}, quiz_id={self.quiz_id}, type='{self.question_type.value}')>"

    def to_dict(self):
        """Convert question to dictionary for API responses"""
        return {
            "id": str(self.id),
            "quiz_id": str(self.quiz_id),
            "question_text": self.question_text,
            "question_type": self.question_type.value,
            "options": self.options or [],
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
            "image_url": self.image_url,
            "audio_url": self.audio_url,
            "difficulty": self.difficulty.value,
            "points": self.points,
            "time_limit": self.time_limit,
            "order_index": self.order_index
        }
    