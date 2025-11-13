"""
Factory Pattern para crear diferentes tipos de preguntas
Implementa el patrón Factory Method para generar preguntas de quiz
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum
import uuid
from datetime import datetime

class QuestionType(Enum):
    """Tipos de preguntas disponibles"""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_IN_BLANK = "fill_in_blank"
    MATCHING = "matching"
    ORDERING = "ordering"
    SHORT_ANSWER = "short_answer"

class DifficultyLevel(Enum):
    """Niveles de dificultad"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

class Question(ABC):
    """Clase base abstracta para todas las preguntas"""
    
    def __init__(self, question_text: str, points: int = 10, time_limit: int = 30,
                 difficulty: DifficultyLevel = DifficultyLevel.MEDIUM,
                 explanation: Optional[str] = None):
        self.id = str(uuid.uuid4())
        self.question_text = question_text
        self.question_type = self.get_question_type()
        self.points = points
        self.time_limit = time_limit
        self.difficulty = difficulty.value
        self.explanation = explanation
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    @abstractmethod
    def get_question_type(self) -> str:
        """Retorna el tipo de pregunta"""
        pass
    
    @abstractmethod
    def validate_answer(self, user_answer: Any) -> bool:
        """Valida si la respuesta del usuario es correcta"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la pregunta a diccionario para guardar en DB"""
        pass
    
    def get_base_dict(self) -> Dict[str, Any]:
        """Datos base comunes a todas las preguntas"""
        return {
            "id": self.id,
            "question_text": self.question_text,
            "question_type": self.question_type,
            "points": self.points,
            "time_limit": self.time_limit,
            "difficulty": self.difficulty,
            "explanation": self.explanation,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class MultipleChoiceQuestion(Question):
    """Pregunta de opción múltiple"""
    
    def __init__(self, question_text: str, options: List[str], correct_answer: int, **kwargs):
        super().__init__(question_text, **kwargs)
        self.options = options
        self.correct_answer = correct_answer
        
        if correct_answer >= len(options) or correct_answer < 0:
            raise ValueError(f"Índice de respuesta correcta {correct_answer} fuera de rango para {len(options)} opciones")
    
    def get_question_type(self) -> str:
        return QuestionType.MULTIPLE_CHOICE.value
    
    def validate_answer(self, user_answer: Any) -> bool:
        return isinstance(user_answer, int) and user_answer == self.correct_answer
    
    def to_dict(self) -> Dict[str, Any]:
        base = self.get_base_dict()
        base.update({
            "options": self.options,
            "correct_answer": self.correct_answer
        })
        return base

class TrueFalseQuestion(Question):
    """Pregunta verdadero/falso"""
    
    def __init__(self, question_text: str, correct_answer: bool, **kwargs):
        super().__init__(question_text, **kwargs)
        self.correct_answer = correct_answer
        self.options = ["Verdadero", "Falso"]
    
    def get_question_type(self) -> str:
        return QuestionType.TRUE_FALSE.value
    
    def validate_answer(self, user_answer: Any) -> bool:
        if isinstance(user_answer, bool):
            return user_answer == self.correct_answer
        elif isinstance(user_answer, int):
            return bool(user_answer) == self.correct_answer
        elif isinstance(user_answer, str):
            return user_answer.lower() in ['true', 'verdadero'] == self.correct_answer
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        base = self.get_base_dict()
        base.update({
            "options": self.options,
            "correct_answer": 0 if self.correct_answer else 1
        })
        return base

class FillInBlankQuestion(Question):
    """Pregunta de llenar espacios en blanco"""
    
    def __init__(self, question_text: str, correct_answers: List[str], case_sensitive: bool = False, **kwargs):
        super().__init__(question_text, **kwargs)
        self.correct_answers = [answer.strip() for answer in correct_answers]
        self.case_sensitive = case_sensitive
        self.options = []  # No hay opciones predefinidas
    
    def get_question_type(self) -> str:
        return QuestionType.FILL_IN_BLANK.value
    
    def validate_answer(self, user_answer: Any) -> bool:
        if not isinstance(user_answer, str):
            return False
        
        user_answer = user_answer.strip()
        if not self.case_sensitive:
            user_answer = user_answer.lower()
            correct_answers = [ans.lower() for ans in self.correct_answers]
        else:
            correct_answers = self.correct_answers
        
        return user_answer in correct_answers
    
    def to_dict(self) -> Dict[str, Any]:
        base = self.get_base_dict()
        base.update({
            "options": self.options,
            "correct_answer": self.correct_answers[0],  # Primera respuesta como principal
            "correct_answers": self.correct_answers,
            "case_sensitive": self.case_sensitive
        })
        return base

class MatchingQuestion(Question):
    """Pregunta de emparejar elementos"""
    
    def __init__(self, question_text: str, pairs: Dict[str, str], **kwargs):
        super().__init__(question_text, **kwargs)
        self.pairs = pairs
        self.left_items = list(pairs.keys())
        self.right_items = list(pairs.values())
        self.options = self.left_items + self.right_items
    
    def get_question_type(self) -> str:
        return QuestionType.MATCHING.value
    
    def validate_answer(self, user_answer: Any) -> bool:
        if not isinstance(user_answer, dict):
            return False
        
        # Verificar que todos los pares coincidan
        for left, right in self.pairs.items():
            if user_answer.get(left) != right:
                return False
        
        return len(user_answer) == len(self.pairs)
    
    def to_dict(self) -> Dict[str, Any]:
        base = self.get_base_dict()
        base.update({
            "options": self.options,
            "correct_answer": self.pairs,
            "pairs": self.pairs,
            "left_items": self.left_items,
            "right_items": self.right_items
        })
        return base

class QuestionFactory:
    """Factory para crear diferentes tipos de preguntas"""
    
    @staticmethod
    def create_question(question_type: str, **kwargs) -> Question:
        """
        Crea una pregunta del tipo especificado
        
        Args:
            question_type: Tipo de pregunta (multiple_choice, true_false, etc.)
            **kwargs: Argumentos específicos para cada tipo de pregunta
        
        Returns:
            Question: Instancia de la pregunta creada
        """
        question_type = question_type.lower()
        
        if question_type == QuestionType.MULTIPLE_CHOICE.value:
            return QuestionFactory._create_multiple_choice(**kwargs)
        elif question_type == QuestionType.TRUE_FALSE.value:
            return QuestionFactory._create_true_false(**kwargs)
        elif question_type == QuestionType.FILL_IN_BLANK.value:
            return QuestionFactory._create_fill_in_blank(**kwargs)
        elif question_type == QuestionType.MATCHING.value:
            return QuestionFactory._create_matching(**kwargs)
        else:
            raise ValueError(f"Tipo de pregunta '{question_type}' no soportado")
    
    @staticmethod
    def _create_multiple_choice(**kwargs) -> MultipleChoiceQuestion:
        """Crear pregunta de opción múltiple"""
        required_fields = ['question_text', 'options', 'correct_answer']
        for field in required_fields:
            if field not in kwargs:
                raise ValueError(f"Campo requerido '{field}' faltante para pregunta de opción múltiple")
        
        return MultipleChoiceQuestion(**kwargs)
    
    @staticmethod
    def _create_true_false(**kwargs) -> TrueFalseQuestion:
        """Crear pregunta verdadero/falso"""
        required_fields = ['question_text', 'correct_answer']
        for field in required_fields:
            if field not in kwargs:
                raise ValueError(f"Campo requerido '{field}' faltante para pregunta verdadero/falso")
        
        return TrueFalseQuestion(**kwargs)
    
    @staticmethod
    def _create_fill_in_blank(**kwargs) -> FillInBlankQuestion:
        """Crear pregunta de llenar espacios"""
        required_fields = ['question_text', 'correct_answers']
        for field in required_fields:
            if field not in kwargs:
                raise ValueError(f"Campo requerido '{field}' faltante para pregunta de llenar espacios")
        
        return FillInBlankQuestion(**kwargs)
    
    @staticmethod
    def _create_matching(**kwargs) -> MatchingQuestion:
        """Crear pregunta de emparejar"""
        required_fields = ['question_text', 'pairs']
        for field in required_fields:
            if field not in kwargs:
                raise ValueError(f"Campo requerido '{field}' faltante para pregunta de emparejar")
        
        return MatchingQuestion(**kwargs)
    
    @staticmethod
    def get_supported_types() -> List[str]:
        """Retorna lista de tipos de preguntas soportados"""
        return [question_type.value for question_type in QuestionType]
    
    @staticmethod
    def create_from_dict(question_data: Dict[str, Any]) -> Question:
        """
        Crea una pregunta desde un diccionario
        
        Args:
            question_data: Diccionario con los datos de la pregunta
        
        Returns:
            Question: Instancia de la pregunta creada
        """
        question_type = question_data.get('question_type')
        if not question_type:
            raise ValueError("Tipo de pregunta no especificado")
        
        return QuestionFactory.create_question(question_type, **question_data)

# Ejemplo de uso y factory preconfigurado para matemáticas
class MathQuestionFactory(QuestionFactory):
    """Factory especializado para preguntas de matemáticas"""
    
    @staticmethod
    def create_arithmetic_question(operation: str, num1: int, num2: int, 
                                 difficulty: DifficultyLevel = DifficultyLevel.MEDIUM) -> MultipleChoiceQuestion:
        """Crear pregunta aritmética automáticamente"""
        operations = {
            '+': (num1 + num2, 'suma'),
            '-': (num1 - num2, 'resta'), 
            '*': (num1 * num2, 'multiplicación'),
            '/': (num1 / num2 if num2 != 0 else 1, 'división')
        }
        
        if operation not in operations:
            raise ValueError(f"Operación '{operation}' no soportada")
        
        correct_answer, op_name = operations[operation]
        correct_answer = int(correct_answer) if operation != '/' else round(correct_answer, 2)
        
        question_text = f"¿Cuánto es {num1} {operation} {num2}?"
        
        # Generar opciones incorrectas
        options = [str(correct_answer)]
        for i in range(3):
            wrong_answer = correct_answer + (-1)**i * (i + 1) * (1 if operation in ['+', '-'] else 2)
            if str(wrong_answer) not in options:
                options.append(str(wrong_answer))
        
        # Mezclar opciones pero recordar la posición correcta
        import random
        correct_index = 0
        random.shuffle(options)
        correct_index = options.index(str(correct_answer))
        
        return MultipleChoiceQuestion(
            question_text=question_text,
            options=options,
            correct_answer=correct_index,
            difficulty=difficulty,
            points=10 if difficulty == DifficultyLevel.EASY else 15 if difficulty == DifficultyLevel.MEDIUM else 20,
            explanation=f"La {op_name} de {num1} y {num2} es {correct_answer}"
        )

if __name__ == "__main__":
    # Ejemplos de uso
    print("🏭 === FACTORY PATTERN PARA PREGUNTAS ===")
    
    # Crear pregunta de opción múltiple
    mc_question = QuestionFactory.create_question(
        "multiple_choice",
        question_text="¿Cuál es la capital de Francia?",
        options=["Madrid", "París", "Roma", "Londres"],
        correct_answer=1,
        points=10
    )
    
    print("✅ Pregunta múltiple choice creada:")
    print(f"   Tipo: {mc_question.question_type}")
    print(f"   ¿París es correcto? {mc_question.validate_answer(1)}")
    
    # Crear pregunta verdadero/falso
    tf_question = QuestionFactory.create_question(
        "true_false",
        question_text="La Tierra es plana",
        correct_answer=False
    )
    
    print("✅ Pregunta verdadero/falso creada:")
    print(f"   ¿False es correcto? {tf_question.validate_answer(False)}")
    
    # Crear pregunta de matemáticas
    math_question = MathQuestionFactory.create_arithmetic_question(
        '+', 15, 25, DifficultyLevel.EASY
    )
    
    print("✅ Pregunta de matemáticas creada:")
    print(f"   Pregunta: {math_question.question_text}")
    print(f"   Opciones: {math_question.options}")
