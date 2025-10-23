from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta

from database.connection import get_db
from services.AuthService import get_current_user, get_current_teacher, get_current_student
from models.User import User
from models.Quiz import Quiz, Class
from models.GameSession import GameSession, ProgressMetrics, SessionStatus
from pydantic import BaseModel

router = APIRouter()

# Pydantic models
class StudentProgressResponse(BaseModel):
    student_id: int
    student_name: str
    total_games_played: int
    average_score: float
    total_time_minutes: int
    last_activity: str = None
    recent_sessions: List[dict]

class ClassProgressResponse(BaseModel):
    class_id: int
    class_name: str
    total_students: int
    active_students: int
    average_class_score: float
    total_games_completed: int
    student_progress: List[Dict[str, Any]]

@router.get("/student/{student_id}", response_model=StudentProgressResponse)
async def get_student_progress(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed progress for a specific student.
    Observer Pattern: Teachers can observe student progress in real-time.
    """
    
    # Authorization check
    if current_user.is_student and current_user.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get student
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # If current user is teacher, verify student is in their class
    if current_user.is_teacher:
        if not student.class_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student is not enrolled in any class"
            )
        
        student_class = db.query(Class).filter(Class.id == student.class_id).first()
        if not student_class or student_class.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student is not in your class"
            )
    
    # Get student's game sessions
    sessions = db.query(GameSession).filter(
        GameSession.student_id == student_id
    ).order_by(GameSession.created_at.desc()).limit(10).all()
    
    # Calculate aggregate statistics
    total_games = len(sessions)
    completed_sessions = [s for s in sessions if s.status == SessionStatus.COMPLETED]
    
    if completed_sessions:
        average_score = sum(s.percentage_score for s in completed_sessions) / len(completed_sessions)
        total_time_minutes = sum(s.duration_minutes for s in completed_sessions)
    else:
        average_score = 0.0
        total_time_minutes = 0.0
    
    # Get recent sessions with quiz information
    recent_sessions = []
    for session in sessions[:5]:  # Last 5 sessions
        quiz = db.query(Quiz).filter(Quiz.id == session.quiz_id).first()
        session_data = session.to_dict()
        session_data["quiz_title"] = quiz.title if quiz else "Unknown Quiz"
        recent_sessions.append(session_data)
    
    # Get last activity
    last_activity = sessions[0].created_at.isoformat() if sessions else None
    
    return StudentProgressResponse(
        student_id=student.id,
        student_name=student.name,
        total_games_played=total_games,
        average_score=round(average_score, 2),
        total_time_minutes=int(total_time_minutes),
        last_activity=last_activity,
        recent_sessions=recent_sessions
    )

@router.get("/class/{class_id}", response_model=ClassProgressResponse)
async def get_class_progress(
    class_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """
    Get progress overview for entire class.
    Observer Pattern: Real-time class performance monitoring.
    """
    
    # Verify teacher owns this class
    class_obj = db.query(Class).filter(
        Class.id == class_id,
        Class.teacher_id == current_user.id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or access denied"
        )
    
    # Get all students in the class
    students = db.query(User).filter(User.class_id == class_id).all()
    
    # Calculate class-wide statistics
    total_students = len(students)
    active_students = 0
    total_games_completed = 0
    class_scores = []
    student_progress = []
    
    # Get recent activity threshold (7 days ago)
    recent_threshold = datetime.utcnow() - timedelta(days=7)
    
    for student in students:
        # Get student's sessions
        sessions = db.query(GameSession).filter(
            GameSession.student_id == student.id
        ).all()
        
        completed_sessions = [s for s in sessions if s.status == SessionStatus.COMPLETED]
        
        # Check if student is active (played in last 7 days)
        recent_sessions = [s for s in sessions if s.created_at >= recent_threshold]
        if recent_sessions:
            active_students += 1
        
        total_games_completed += len(completed_sessions)
        
        # Calculate student statistics
        if completed_sessions:
            avg_score = sum(s.percentage_score for s in completed_sessions) / len(completed_sessions)
            total_time = sum(s.duration_minutes for s in completed_sessions)
            class_scores.append(avg_score)
        else:
            avg_score = 0.0
            total_time = 0.0
        
        student_data = {
            "student_id": student.id,
            "student_name": student.name,
            "games_played": len(sessions),
            "games_completed": len(completed_sessions),
            "average_score": round(avg_score, 2),
            "total_time_minutes": int(total_time),
            "is_active": len(recent_sessions) > 0,
            "last_activity": max(s.created_at for s in sessions).isoformat() if sessions else None
        }
        
        student_progress.append(student_data)
    
    # Calculate class average
    average_class_score = sum(class_scores) / len(class_scores) if class_scores else 0.0
    
    return ClassProgressResponse(
        class_id=class_obj.id,
        class_name=class_obj.name,
        total_students=total_students,
        active_students=active_students,
        average_class_score=round(average_class_score, 2),
        total_games_completed=total_games_completed,
        student_progress=student_progress
    )

@router.get("/metrics")
async def get_progress_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive progress metrics.
    Observer Pattern: Aggregated metrics updated when sessions complete.
    """
    
    if current_user.is_student:
        # Get student's personal metrics
        return await get_student_progress(current_user.id, current_user, db)
    
    else:
        # Get teacher's class metrics
        classes = db.query(Class).filter(Class.teacher_id == current_user.id).all()
        
        if not classes:
            return {
                "message": "No classes found",
                "classes": []
            }
        
        # Get metrics for all teacher's classes
        all_metrics = []
        for class_obj in classes:
            try:
                class_metrics = await get_class_progress(class_obj.id, current_user, db)
                all_metrics.append(class_metrics.dict())
            except HTTPException:
                continue
        
        return {
            "teacher_id": current_user.id,
            "teacher_name": current_user.name,
            "total_classes": len(classes),
            "classes": all_metrics
        }

@router.get("/analytics/quiz/{quiz_id}")
async def get_quiz_analytics(
    quiz_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """
    Get detailed analytics for a specific quiz.
    """
    
    # Verify teacher owns this quiz
    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id,
        Quiz.creator_id == current_user.id
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found or access denied"
        )
    
    # Get all sessions for this quiz
    sessions = db.query(GameSession).filter(GameSession.quiz_id == quiz_id).all()
    
    if not sessions:
        return {
            "quiz_id": quiz_id,
            "quiz_title": quiz.title,
            "total_attempts": 0,
            "analytics": "No attempts yet"
        }
    
    # Calculate analytics
    completed_sessions = [s for s in sessions if s.status == SessionStatus.COMPLETED]
    
    analytics = {
        "quiz_id": quiz_id,
        "quiz_title": quiz.title,
        "total_attempts": len(sessions),
        "completed_attempts": len(completed_sessions),
        "completion_rate": len(completed_sessions) / len(sessions) * 100 if sessions else 0,
        "average_score": sum(s.percentage_score for s in completed_sessions) / len(completed_sessions) if completed_sessions else 0,
        "average_time_minutes": sum(s.duration_minutes for s in completed_sessions) / len(completed_sessions) if completed_sessions else 0,
        "difficulty_analysis": {
            "scores_by_difficulty": {},
            "time_by_difficulty": {}
        },
        "question_analysis": []
    }
    
    # Analyze by questions (simplified)
    from models.GameSession import Answer
    for question in quiz.questions:
        answers = db.query(Answer).filter(Answer.question_id == question.id).all()
        
        if answers:
            correct_count = sum(1 for a in answers if a.is_correct)
            avg_time = sum(a.time_taken_seconds for a in answers) / len(answers)
            
            question_stats = {
                "question_id": question.id,
                "question_text": question.question_text[:100] + "..." if len(question.question_text) > 100 else question.question_text,
                "total_answers": len(answers),
                "correct_answers": correct_count,
                "accuracy_rate": correct_count / len(answers) * 100,
                "average_time_seconds": int(avg_time),
                "difficulty": question.difficulty.value
            }
            
            analytics["question_analysis"].append(question_stats)
    
    return analytics
