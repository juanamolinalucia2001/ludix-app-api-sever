from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base
import enum
from datetime import datetime
from typing import Dict, Any

class SessionStatus(enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    ABANDONED = "abandoned"

class GameSession(Base):
    """
    Game session model to track student progress through quizzes.
    Observer Pattern: Notifies teachers of student progress.
    """
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    
    # Session tracking
    status = Column(Enum(SessionStatus), default=SessionStatus.IN_PROGRESS)
    current_question = Column(Integer, default=0)
    score = Column(Integer, default=0)
    total_questions = Column(Integer, nullable=False)
    
    # Timing
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    total_time_seconds = Column(Integer, nullable=True)
    
    # Additional metrics
    correct_answers = Column(Integer, default=0)
    incorrect_answers = Column(Integer, default=0)
    hints_used = Column(Integer, default=0)
    
    # Session metadata
    device_info = Column(JSON, nullable=True)  # Browser, OS, etc.
    ip_address = Column(String(45), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    student = relationship("User", back_populates="game_sessions")
    quiz = relationship("Quiz", back_populates="game_sessions")
    answers = relationship("Answer", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<GameSession(id={self.id}, student_id={self.student_id}, quiz_id={self.quiz_id}, status='{self.status.value}')>"

    @property
    def percentage_score(self) -> float:
        if self.total_questions == 0:
            return 0.0
        return (self.score / self.total_questions) * 100

    @property
    def is_completed(self) -> bool:
        return self.status == SessionStatus.COMPLETED

    @property
    def duration_minutes(self) -> float:
        if self.end_time and self.start_time:
            duration = self.end_time - self.start_time
            return duration.total_seconds() / 60
        return 0.0

    def to_dict(self, include_answers: bool = False):
        """Convert session to dictionary for API responses"""
        data = {
            "id": self.id,
            "student_id": self.student_id,
            "quiz_id": self.quiz_id,
            "status": self.status.value,
            "current_question": self.current_question,
            "score": self.score,
            "total_questions": self.total_questions,
            "correct_answers": self.correct_answers,
            "incorrect_answers": self.incorrect_answers,
            "hints_used": self.hints_used,
            "percentage_score": round(self.percentage_score, 2),
            "duration_minutes": round(self.duration_minutes, 2),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_time_seconds": self.total_time_seconds
        }
        
        if include_answers:
            data["answers"] = [answer.to_dict() for answer in self.answers]
            
        return data

class Answer(Base):
    """
    Individual answer tracking for detailed analytics.
    Observer Pattern: Each answer can trigger progress notifications.
    """
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    
    # Answer data
    selected_answer = Column(Integer, nullable=False)  # Index of selected option
    is_correct = Column(Boolean, nullable=False)
    time_taken_seconds = Column(Integer, nullable=False)
    
    # Additional tracking
    attempts = Column(Integer, default=1)  # Number of attempts for this question
    hint_used = Column(Boolean, default=False)
    confidence_level = Column(Integer, nullable=True)  # 1-5 scale
    
    # Timestamps
    answered_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("GameSession", back_populates="answers")
    question = relationship("Question", back_populates="answers")

    def __repr__(self):
        return f"<Answer(id={self.id}, session_id={self.session_id}, question_id={self.question_id}, correct={self.is_correct})>"

    def to_dict(self):
        """Convert answer to dictionary for API responses"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "question_id": self.question_id,
            "selected_answer": self.selected_answer,
            "is_correct": self.is_correct,
            "time_taken_seconds": self.time_taken_seconds,
            "attempts": self.attempts,
            "hint_used": self.hint_used,
            "confidence_level": self.confidence_level,
            "answered_at": self.answered_at.isoformat() if self.answered_at else None
        }

class ProgressMetrics(Base):
    """
    Aggregated progress metrics for students and classes.
    Observer Pattern: Updated when game sessions complete.
    """
    __tablename__ = "progress_metrics"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    
    # Aggregated metrics
    total_games_played = Column(Integer, default=0)
    total_questions_answered = Column(Integer, default=0)
    total_correct_answers = Column(Integer, default=0)
    total_time_spent_minutes = Column(Integer, default=0)
    
    # Performance metrics
    average_score = Column(Float, default=0.0)
    best_score = Column(Float, default=0.0)
    current_streak = Column(Integer, default=0)  # Consecutive correct answers
    longest_streak = Column(Integer, default=0)
    
    # Learning analytics
    preferred_topics = Column(JSON, nullable=True)  # Array of topics with scores
    common_mistakes = Column(JSON, nullable=True)  # Array of frequently missed questions
    improvement_areas = Column(JSON, nullable=True)  # Suggested areas for improvement
    
    # Engagement metrics
    last_activity = Column(DateTime(timezone=True), nullable=True)
    weekly_activity_minutes = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    student = relationship("User")
    class_obj = relationship("Class")

    def __repr__(self):
        return f"<ProgressMetrics(id={self.id}, student_id={self.student_id}, avg_score={self.average_score})>"

    def to_dict(self):
        """Convert metrics to dictionary for API responses"""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "class_id": self.class_id,
            "total_games_played": self.total_games_played,
            "total_questions_answered": self.total_questions_answered,
            "total_correct_answers": self.total_correct_answers,
            "total_time_spent_minutes": self.total_time_spent_minutes,
            "average_score": round(self.average_score, 2),
            "best_score": round(self.best_score, 2),
            "current_streak": self.current_streak,
            "longest_streak": self.longest_streak,
            "preferred_topics": self.preferred_topics or [],
            "common_mistakes": self.common_mistakes or [],
            "improvement_areas": self.improvement_areas or [],
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "weekly_activity_minutes": self.weekly_activity_minutes,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
