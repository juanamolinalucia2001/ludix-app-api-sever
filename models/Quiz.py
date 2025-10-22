"""
Quiz model using SQLAlchemy ORM.
Factory pattern: Quizzes are created as content objects.
Observer pattern: Quiz progress can be tracked through attempts.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from db.base import Base


class Quiz(Base):
    """
    Quiz model representing quiz content.
    Factory pattern: Represents content created by the content factory.
    """
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    difficulty_level = Column(String(20), nullable=False, default="beginner")  # beginner, intermediate, advanced
    category = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    # questions = relationship("Question", back_populates="quiz")
    # attempts = relationship("QuizAttempt", back_populates="quiz")

    def __repr__(self):
        return f"<Quiz(id={self.id}, title='{self.title}', difficulty='{self.difficulty_level}')>"
