#!/usr/bin/env python3
"""
Script para inicializar la base de datos con datos de ejemplo.
Ejecutar: python init_db.py
"""

import sys
import os
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import engine, Base, SessionLocal
from models.User import User, UserRole
from models.Quiz import Class, Quiz, Question, DifficultyLevel, QuestionType
from models.GameSession import GameSession, SessionStatus
from services.AuthService import auth_service
import secrets
import string

def generate_class_code() -> str:
    """Generate a unique 6-character class code"""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

def init_database():
    """Initialize database with sample data"""
    print("🚀 Iniciando configuración de base de datos...")
    
    # Create all tables
    print("📋 Creando tablas...")
    Base.metadata.create_all(bind=engine)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_users = db.query(User).count()
        if existing_users > 0:
            print("✅ La base de datos ya tiene datos. Saltando inicialización.")
            return
        
        print("👩‍🏫 Creando docente de ejemplo...")
        # Create sample teacher
        teacher = User(
            email="docente@ludix.com",
            name="Profesor Juan Carlos",
            hashed_password=auth_service.hash_password("123456"),  # Contraseña más corta
            role=UserRole.TEACHER,
            is_active=True
        )
        db.add(teacher)
        db.flush()  # Get the teacher ID
        
        print("🏫 Creando clase de ejemplo...")
        # Create sample class
        sample_class = Class(
            name="3° Grado A",
            description="Clase de tercer grado - Matemáticas y Lectura",
            teacher_id=teacher.id,
            class_code=generate_class_code(),
            max_students=30
        )
        db.add(sample_class)
        db.flush()  # Get the class ID
        
        print("👨‍🎓 Creando estudiantes de ejemplo...")
        # Create sample students
        students = [
            {"name": "Ana Martínez", "email": "ana@estudiante.com", "mascot": "unicorn"},
            {"name": "Carlos López", "email": "carlos@estudiante.com", "mascot": "dragon"},
            {"name": "Sofía Rodríguez", "email": "sofia@estudiante.com", "mascot": "cat"},
            {"name": "Diego Fernández", "email": "diego@estudiante.com", "mascot": "robot"},
            {"name": "Emma Silva", "email": "emma@estudiante.com", "mascot": "dog"}
        ]
        
        for student_data in students:
            student = User(
                email=student_data["email"],
                name=student_data["name"],
                hashed_password=auth_service.hash_password("123456"),
                role=UserRole.STUDENT,
                class_id=sample_class.id,
                mascot=student_data["mascot"],
                is_active=True
            )
            db.add(student)
        
        db.flush()  # Save students
        
        print("📚 Creando quiz de ejemplo...")
        # Create sample quiz
        quiz = Quiz(
            title="Matemáticas Básicas",
            description="Sumas y restas para tercer grado",
            creator_id=teacher.id,
            class_id=sample_class.id,
            time_limit=600,  # 10 minutes
            difficulty=DifficultyLevel.EASY,
            topic="matemáticas",
            is_published=True,
            published_at=datetime.utcnow()
        )
        db.add(quiz)
        db.flush()  # Get the quiz ID
        
        print("❓ Creando preguntas de ejemplo...")
        # Create sample questions
        questions = [
            {
                "text": "¿Cuánto es 2 + 3?",
                "options": ["4", "5", "6", "7"],
                "correct": 1,
                "explanation": "2 + 3 = 5"
            },
            {
                "text": "¿Cuánto es 8 - 3?",
                "options": ["4", "5", "6", "3"],
                "correct": 1,
                "explanation": "8 - 3 = 5"
            },
            {
                "text": "¿Cuánto es 4 + 4?",
                "options": ["6", "7", "8", "9"],
                "correct": 2,
                "explanation": "4 + 4 = 8"
            },
            {
                "text": "¿Cuánto es 10 - 6?",
                "options": ["3", "4", "5", "6"],
                "correct": 1,
                "explanation": "10 - 6 = 4"
            },
            {
                "text": "¿Cuánto es 3 + 7?",
                "options": ["9", "10", "11", "12"],
                "correct": 1,
                "explanation": "3 + 7 = 10"
            }
        ]
        
        for idx, q_data in enumerate(questions):
            question = Question(
                quiz_id=quiz.id,
                question_text=q_data["text"],
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=q_data["options"],
                correct_answer=q_data["correct"],
                explanation=q_data["explanation"],
                difficulty=DifficultyLevel.EASY,
                points=1,
                order_index=idx
            )
            db.add(question)
        
        # Commit all changes
        db.commit()
        
        print("\n✅ ¡Base de datos inicializada correctamente!")
        print("\n📋 Datos de acceso creados:")
        print("👩‍🏫 DOCENTE:")
        print(f"   Email: docente@ludix.com")
        print(f"   Password: password123")
        print(f"   Clase: {sample_class.name}")
        print(f"   Código de clase: {sample_class.class_code}")
        print("\n👨‍🎓 ESTUDIANTES:")
        print(f"   Email: ana@estudiante.com (password: student123)")
        print(f"   Email: carlos@estudiante.com (password: student123)")
        print(f"   Email: sofia@estudiante.com (password: student123)")
        print(f"   Email: diego@estudiante.com (password: student123)")
        print(f"   Email: emma@estudiante.com (password: student123)")
        print(f"\n📚 Quiz creado: '{quiz.title}' con {len(questions)} preguntas")
        print("\n🚀 ¡Ya puedes iniciar la aplicación!")
        
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
