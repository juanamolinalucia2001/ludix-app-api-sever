from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.connection import get_db
from services.AuthService import get_current_user, get_current_teacher
from models.User import User
from models.Quiz import Quiz, Question, DifficultyLevel, QuestionType
from pydantic import BaseModel

router = APIRouter()

# Pydantic models
class QuestionCreate(BaseModel):
    question_text: str
    question_type: str = "multiple_choice"
    options: List[str]
    correct_answer: int
    explanation: str = None
    difficulty: str = "easy"
    points: int = 1

class QuizCreate(BaseModel):
    title: str
    description: str = None
    time_limit: int = None
    difficulty: str = "easy"
    topic: str = None
    questions: List[QuestionCreate]

class TextContent(BaseModel):
    title: str
    content: str
    topic: str = None

@router.post("/quizzes", response_model=dict)
async def create_quiz(
    quiz_data: QuizCreate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """
    Create a new quiz with questions.
    Factory Pattern: Creates quiz and questions based on input data.
    """
    
    # Get teacher's first class (simplified for MVP)
    from models.Quiz import Class
    teacher_class = db.query(Class).filter(Class.teacher_id == current_user.id).first()
    
    if not teacher_class:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must create a class before creating quizzes"
        )
    
    # Validate difficulty
    try:
        difficulty = DifficultyLevel(quiz_data.difficulty)
    except ValueError:
        difficulty = DifficultyLevel.EASY
    
    # Create quiz
    new_quiz = Quiz(
        title=quiz_data.title,
        description=quiz_data.description,
        creator_id=current_user.id,
        class_id=teacher_class.id,
        time_limit=quiz_data.time_limit,
        difficulty=difficulty,
        topic=quiz_data.topic
    )
    
    db.add(new_quiz)
    db.flush()  # Get the quiz ID
    
    # Create questions
    for idx, question_data in enumerate(quiz_data.questions):
        # Validate question type
        try:
            q_type = QuestionType(question_data.question_type)
        except ValueError:
            q_type = QuestionType.MULTIPLE_CHOICE
        
        # Validate difficulty
        try:
            q_difficulty = DifficultyLevel(question_data.difficulty)
        except ValueError:
            q_difficulty = DifficultyLevel.EASY
        
        question = Question(
            quiz_id=new_quiz.id,
            question_text=question_data.question_text,
            question_type=q_type,
            options=question_data.options,
            correct_answer=question_data.correct_answer,
            explanation=question_data.explanation,
            difficulty=q_difficulty,
            points=question_data.points,
            order_index=idx
        )
        
        db.add(question)
    
    db.commit()
    db.refresh(new_quiz)
    
    return {
        "message": "Quiz created successfully",
        "quiz": new_quiz.to_dict(include_questions=True)
    }

@router.get("/quizzes", response_model=List[dict])
async def get_quizzes(
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get all quizzes created by the teacher"""
    
    quizzes = db.query(Quiz).filter(Quiz.creator_id == current_user.id).all()
    
    return [quiz.to_dict(include_questions=False) for quiz in quizzes]

@router.get("/quizzes/{quiz_id}", response_model=dict)
async def get_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific quiz with questions"""
    
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Authorization check
    if current_user.is_teacher and quiz.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if current_user.is_student and (quiz.class_id != current_user.class_id or not quiz.is_published):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quiz not available"
        )
    
    return quiz.to_dict(include_questions=True)

@router.put("/quizzes/{quiz_id}/publish")
async def publish_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Publish a quiz to make it available to students"""
    
    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id,
        Quiz.creator_id == current_user.id
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found or access denied"
        )
    
    if len(quiz.questions) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot publish quiz without questions"
        )
    
    quiz.is_published = True
    quiz.published_at = db.func.now()
    db.commit()
    
    return {"message": "Quiz published successfully"}

@router.delete("/quizzes/{quiz_id}")
async def delete_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Delete a quiz and all its questions"""
    
    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id,
        Quiz.creator_id == current_user.id
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found or access denied"
        )
    
    # Check if quiz has been attempted by students
    from models.GameSession import GameSession
    session_count = db.query(GameSession).filter(GameSession.quiz_id == quiz_id).count()
    
    if session_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete quiz that has been attempted by students"
        )
    
    db.delete(quiz)
    db.commit()
    
    return {"message": "Quiz deleted successfully"}

@router.post("/texts", response_model=dict)
async def create_text_content(
    text_data: TextContent,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Create text content (for future reading comprehension features)"""
    
    # This is a placeholder for text content creation
    # In a full implementation, you'd have a TextContent model
    
    return {
        "message": "Text content creation will be implemented in the next iteration",
        "data": text_data.dict()
    }

@router.post("/upload")
async def upload_content(
    current_user: User = Depends(get_current_teacher),
):
    """Upload files (images, audio) for quiz content"""
    
    # This is a placeholder for file upload functionality
    # In a full implementation, you'd handle file uploads here
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="File upload will be implemented in the next iteration"
    )
