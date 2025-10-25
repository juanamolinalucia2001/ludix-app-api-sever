from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database.connection import get_db
from services.AuthService import get_current_user, get_current_teacher, get_current_student
from models.User import User
from models.Quiz import Quiz
from models.GameSession import GameSession, SessionStatus, Answer
from pydantic import BaseModel

router = APIRouter()

# Pydantic models
class GameSessionCreate(BaseModel):
    quiz_id: int

class AnswerSubmit(BaseModel):
    question_id: int
    selected_answer: int
    time_taken_seconds: int
    hint_used: bool = False
    confidence_level: Optional[int] = None

class GameSessionResponse(BaseModel):
    id: int
    quiz_id: int
    status: str
    current_question: int
    score: int
    total_questions: int
    start_time: str
    quiz_title: str

@router.get("/", response_model=List[dict])
async def get_available_games(
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    Get available quizzes/games for a student.
    Observer Pattern: Can notify teachers when students view available games.
    """
    if not current_user.class_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student must be enrolled in a class"
        )
    
    # Get published quizzes for the student's class
    quizzes = db.query(Quiz).filter(
        Quiz.class_id == current_user.class_id,
        Quiz.is_published == True,
        Quiz.is_active == True
    ).order_by(Quiz.order_index, Quiz.created_at).all()
    
    # Convert to response format
    games = []
    for quiz in quizzes:
        # Get student's previous sessions for this quiz
        last_session = db.query(GameSession).filter(
            GameSession.student_id == current_user.id,
            GameSession.quiz_id == quiz.id
        ).order_by(GameSession.created_at.desc()).first()
        
        game_data = quiz.to_dict(include_questions=False)
        game_data.update({
            "last_played": last_session.created_at.isoformat() if last_session else None,
            "best_score": last_session.score if last_session and last_session.is_completed else None,
            "can_play": True  # Add logic for play restrictions if needed
        })
        games.append(game_data)
    
    return games

@router.post("/{quiz_id}/start", response_model=GameSessionResponse)
async def start_game_session(
    quiz_id: int,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    Start a new game session for a student.
    Factory Pattern: Creates new game session based on quiz and student.
    """
    # Validate quiz exists and is accessible
    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id,
        Quiz.class_id == current_user.class_id,
        Quiz.is_published == True,
        Quiz.is_active == True
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found or not accessible"
        )
    
    # Check if student has an active session
    active_session = db.query(GameSession).filter(
        GameSession.student_id == current_user.id,
        GameSession.quiz_id == quiz_id,
        GameSession.status == SessionStatus.IN_PROGRESS
    ).first()
    
    if active_session:
        # Return existing session
        return GameSessionResponse(
            id=active_session.id,
            quiz_id=active_session.quiz_id,
            status=active_session.status.value,
            current_question=active_session.current_question,
            score=active_session.score,
            total_questions=active_session.total_questions,
            start_time=active_session.start_time.isoformat(),
            quiz_title=quiz.title
        )
    
    # Create new game session
    new_session = GameSession(
        student_id=current_user.id,
        quiz_id=quiz_id,
        total_questions=len(quiz.questions),
        status=SessionStatus.IN_PROGRESS
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return GameSessionResponse(
        id=new_session.id,
        quiz_id=new_session.quiz_id,
        status=new_session.status.value,
        current_question=new_session.current_question,
        score=new_session.score,
        total_questions=new_session.total_questions,
        start_time=new_session.start_time.isoformat(),
        quiz_title=quiz.title
    )

@router.post("/sessions/{session_id}/answer")
async def submit_answer(
    session_id: int,
    answer_data: AnswerSubmit,
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    Submit an answer for a question in a game session.
    Observer Pattern: Can notify teachers of student progress in real-time.
    """
    # Get session and validate ownership
    session = db.query(GameSession).filter(
        GameSession.id == session_id,
        GameSession.student_id == current_user.id,
        GameSession.status == SessionStatus.IN_PROGRESS
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found or not active"
        )
    
    # Get quiz and current question
    quiz = db.query(Quiz).filter(Quiz.id == session.quiz_id).first()
    if not quiz or session.current_question >= len(quiz.questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid question or session completed"
        )
    
    current_question = quiz.questions[session.current_question]
    
    # Validate question ID
    if current_question.id != answer_data.question_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question ID does not match current question"
        )
    
    # Check if answer is correct
    is_correct = current_question.correct_answer == answer_data.selected_answer
    
    # Create answer record
    answer = Answer(
        session_id=session_id,
        question_id=answer_data.question_id,
        selected_answer=answer_data.selected_answer,
        is_correct=is_correct,
        time_taken_seconds=answer_data.time_taken_seconds,
        hint_used=answer_data.hint_used,
        confidence_level=answer_data.confidence_level
    )
    
    db.add(answer)
    
    # Update session
    if is_correct:
        session.correct_answers += 1
        session.score += current_question.points
    else:
        session.incorrect_answers += 1
    
    if answer_data.hint_used:
        session.hints_used += 1
    
    session.current_question += 1
    
    # Check if session is complete
    if session.current_question >= session.total_questions:
        session.status = SessionStatus.COMPLETED
        session.end_time = db.func.now()
        
        # Calculate total time
        if session.start_time and session.end_time:
            duration = session.end_time - session.start_time
            session.total_time_seconds = int(duration.total_seconds())
    
    db.commit()
    
    # Return session status and next question info
    response = {
        "session_id": session.id,
        "question_answered": answer_data.question_id,
        "is_correct": is_correct,
        "current_score": session.score,
        "current_question": session.current_question,
        "total_questions": session.total_questions,
        "session_completed": session.status == SessionStatus.COMPLETED
    }
    
    if session.status == SessionStatus.COMPLETED:
        response.update({
            "final_score": session.score,
            "correct_answers": session.correct_answers,
            "incorrect_answers": session.incorrect_answers,
            "percentage_score": session.percentage_score,
            "total_time_seconds": session.total_time_seconds
        })
    else:
        # Include next question data
        next_question = quiz.questions[session.current_question]
        response["next_question"] = next_question.to_dict()
    
    return response

@router.get("/sessions/{session_id}/results")
async def get_session_results(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed results for a completed game session.
    Teachers can view any session in their class, students only their own.
    """
    # Get session
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found"
        )
    
    # Authorization check
    if current_user.is_student and session.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if current_user.is_teacher:
        # Check if session belongs to teacher's class
        quiz = db.query(Quiz).filter(Quiz.id == session.quiz_id).first()
        if not quiz or quiz.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Get detailed session data with answers
    session_data = session.to_dict(include_answers=True)
    
    # Add quiz information
    quiz = db.query(Quiz).filter(Quiz.id == session.quiz_id).first()
    session_data["quiz"] = quiz.to_dict(include_questions=True)
    
    # Add student information (for teachers)
    if current_user.is_teacher:
        student = db.query(User).filter(User.id == session.student_id).first()
        session_data["student"] = {
            "id": student.id,
            "name": student.name,
            "email": student.email
        }
    
    return session_data

@router.get("/history")
async def get_game_history(
    current_user: User = Depends(get_current_student),
    db: Session = Depends(get_db),
    limit: int = 10,
    offset: int = 0
):
    """
    Get game history for a student.
    """
    sessions = db.query(GameSession).filter(
        GameSession.student_id == current_user.id
    ).order_by(GameSession.created_at.desc()).offset(offset).limit(limit).all()
    
    history = []
    for session in sessions:
        quiz = db.query(Quiz).filter(Quiz.id == session.quiz_id).first()
        session_data = session.to_dict()
        session_data["quiz_title"] = quiz.title if quiz else "Unknown Quiz"
        history.append(session_data)
    
    return {
        "sessions": history,
        "total": len(history),
        "limit": limit,
        "offset": offset
    }
