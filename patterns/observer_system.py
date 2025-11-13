"""
Observer Pattern para el sistema de eventos y notificaciones de Ludix
Permite notificar automáticamente cuando ocurren eventos importantes
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import asyncio
import json

class EventType(Enum):
    """Tipos de eventos del sistema"""
    USER_REGISTERED = "user_registered"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    CLASS_CREATED = "class_created"
    STUDENT_JOINED_CLASS = "student_joined_class"
    QUIZ_CREATED = "quiz_created"
    GAME_SESSION_STARTED = "game_session_started"
    GAME_SESSION_COMPLETED = "game_session_completed"
    ANSWER_SUBMITTED = "answer_submitted"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    PROGRESS_UPDATED = "progress_updated"

class Event:
    """Clase que representa un evento del sistema"""
    
    def __init__(self, event_type: EventType, data: Dict[str, Any], 
                 user_id: Optional[str] = None, metadata: Optional[Dict] = None):
        self.id = f"evt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(self)}"
        self.event_type = event_type
        self.data = data
        self.user_id = user_id
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el evento a diccionario"""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "data": self.data,
            "user_id": self.user_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    def __str__(self):
        return f"Event({self.event_type.value}, user={self.user_id}, time={self.timestamp})"

class Observer(ABC):
    """Interface para observadores"""
    
    @abstractmethod
    async def update(self, event: Event) -> None:
        """Método llamado cuando ocurre un evento"""
        pass
    
    @abstractmethod
    def get_interested_events(self) -> List[EventType]:
        """Retorna los tipos de eventos en los que está interesado este observador"""
        pass
    
    @abstractmethod
    def get_observer_name(self) -> str:
        """Retorna el nombre del observador"""
        pass

class Subject(ABC):
    """Interface para sujetos observables"""
    
    @abstractmethod
    def attach(self, observer: Observer) -> None:
        """Adjuntar un observador"""
        pass
    
    @abstractmethod
    def detach(self, observer: Observer) -> None:
        """Quitar un observador"""
        pass
    
    @abstractmethod
    async def notify(self, event: Event) -> None:
        """Notificar a todos los observadores relevantes"""
        pass

class EventManager(Subject):
    """Gestor central de eventos - implementa Subject"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.observers = []
            cls._instance.event_history = []
        return cls._instance
    
    def attach(self, observer: Observer) -> None:
        """Adjuntar un observador"""
        if observer not in self.observers:
            self.observers.append(observer)
            print(f"🔗 Observer '{observer.get_observer_name()}' adjuntado")
    
    def detach(self, observer: Observer) -> None:
        """Quitar un observador"""
        if observer in self.observers:
            self.observers.remove(observer)
            print(f"🔓 Observer '{observer.get_observer_name()}' removido")
    
    async def notify(self, event: Event) -> None:
        """Notificar a observadores interesados en este tipo de evento"""
        self.event_history.append(event)
        
        print(f"📢 Evento emitido: {event}")
        
        for observer in self.observers:
            if event.event_type in observer.get_interested_events():
                try:
                    await observer.update(event)
                except Exception as e:
                    print(f"❌ Error en observer {observer.get_observer_name()}: {e}")
    
    async def emit_event(self, event_type: EventType, data: Dict[str, Any], 
                        user_id: Optional[str] = None, metadata: Optional[Dict] = None) -> None:
        """Emitir un nuevo evento"""
        event = Event(event_type, data, user_id, metadata)
        await self.notify(event)
    
    def get_event_history(self, limit: int = 50) -> List[Event]:
        """Obtener historial de eventos"""
        return self.event_history[-limit:]
    
    def get_observers_count(self) -> int:
        """Obtener número de observadores registrados"""
        return len(self.observers)

# === IMPLEMENTACIONES CONCRETAS DE OBSERVERS ===

class ProgressTracker(Observer):
    """Observer que rastrea el progreso de los estudiantes"""
    
    def __init__(self):
        self.student_progress = {}
    
    async def update(self, event: Event) -> None:
        """Actualizar progreso según el evento"""
        if event.event_type == EventType.GAME_SESSION_COMPLETED:
            student_id = event.user_id
            score = event.data.get('score', 0)
            
            if student_id not in self.student_progress:
                self.student_progress[student_id] = {
                    'total_games': 0,
                    'total_score': 0,
                    'best_score': 0,
                    'last_activity': None
                }
            
            progress = self.student_progress[student_id]
            progress['total_games'] += 1
            progress['total_score'] += score
            progress['best_score'] = max(progress['best_score'], score)
            progress['last_activity'] = event.timestamp
            
            print(f"📊 Progreso actualizado para estudiante {student_id}: {progress}")
    
    def get_interested_events(self) -> List[EventType]:
        return [
            EventType.GAME_SESSION_COMPLETED,
            EventType.ANSWER_SUBMITTED,
            EventType.ACHIEVEMENT_UNLOCKED
        ]
    
    def get_observer_name(self) -> str:
        return "ProgressTracker"
    
    def get_student_progress(self, student_id: str) -> Optional[Dict]:
        """Obtener progreso de un estudiante específico"""
        return self.student_progress.get(student_id)

class AchievementSystem(Observer):
    """Observer que maneja logros y insignias"""
    
    def __init__(self):
        self.achievements = {
            'first_game': {'name': 'Primer Juego', 'description': 'Completó su primer juego'},
            'perfect_score': {'name': 'Puntuación Perfecta', 'description': 'Obtuvo 100% en un juego'},
            'speed_demon': {'name': 'Demonio de Velocidad', 'description': 'Completó un juego en menos de 2 minutos'},
            'persistent': {'name': 'Persistente', 'description': 'Jugó 10 juegos'},
            'class_joiner': {'name': 'Socializer', 'description': 'Se unió a una clase'}
        }
        self.user_achievements = {}
    
    async def update(self, event: Event) -> None:
        """Verificar si se desbloqueó algún logro"""
        user_id = event.user_id
        if not user_id:
            return
        
        if user_id not in self.user_achievements:
            self.user_achievements[user_id] = []
        
        unlocked = []
        
        if event.event_type == EventType.GAME_SESSION_COMPLETED:
            # Primer juego
            if 'first_game' not in self.user_achievements[user_id]:
                unlocked.append('first_game')
            
            # Puntuación perfecta
            score = event.data.get('score', 0)
            total_questions = event.data.get('total_questions', 1)
            if score == total_questions * 10 and 'perfect_score' not in self.user_achievements[user_id]:
                unlocked.append('perfect_score')
        
        elif event.event_type == EventType.STUDENT_JOINED_CLASS:
            if 'class_joiner' not in self.user_achievements[user_id]:
                unlocked.append('class_joiner')
        
        # Agregar logros desbloqueados
        for achievement_id in unlocked:
            if achievement_id not in self.user_achievements[user_id]:
                self.user_achievements[user_id].append(achievement_id)
                
                # Emitir evento de logro desbloqueado
                await EventManager().emit_event(
                    EventType.ACHIEVEMENT_UNLOCKED,
                    {
                        'achievement_id': achievement_id,
                        'achievement': self.achievements[achievement_id]
                    },
                    user_id
                )
                
                print(f"🏆 ¡Logro desbloqueado! {self.achievements[achievement_id]['name']} para usuario {user_id}")
    
    def get_interested_events(self) -> List[EventType]:
        return [
            EventType.GAME_SESSION_COMPLETED,
            EventType.STUDENT_JOINED_CLASS,
            EventType.USER_REGISTERED
        ]
    
    def get_observer_name(self) -> str:
        return "AchievementSystem"

class NotificationService(Observer):
    """Observer que maneja notificaciones push/email"""
    
    def __init__(self):
        self.notifications_sent = []
    
    async def update(self, event: Event) -> None:
        """Enviar notificaciones según el evento"""
        notification = None
        
        if event.event_type == EventType.STUDENT_JOINED_CLASS:
            class_name = event.data.get('class_name', 'una clase')
            notification = {
                'user_id': event.user_id,
                'title': '¡Bienvenido a la clase!',
                'message': f'Te has unido exitosamente a {class_name}',
                'type': 'success'
            }
        
        elif event.event_type == EventType.ACHIEVEMENT_UNLOCKED:
            achievement = event.data.get('achievement', {})
            notification = {
                'user_id': event.user_id,
                'title': '🏆 ¡Nuevo logro!',
                'message': f'Has desbloqueado: {achievement.get("name", "Logro")}',
                'type': 'achievement'
            }
        
        elif event.event_type == EventType.QUIZ_CREATED:
            notification = {
                'user_id': event.user_id,
                'title': '📝 Nuevo quiz disponible',
                'message': f'Se ha creado el quiz: {event.data.get("title", "Sin título")}',
                'type': 'info'
            }
        
        if notification:
            notification['timestamp'] = event.timestamp
            notification['event_id'] = event.id
            self.notifications_sent.append(notification)
            print(f"📨 Notificación enviada: {notification['title']} para usuario {notification['user_id']}")
    
    def get_interested_events(self) -> List[EventType]:
        return [
            EventType.STUDENT_JOINED_CLASS,
            EventType.ACHIEVEMENT_UNLOCKED,
            EventType.QUIZ_CREATED,
            EventType.GAME_SESSION_COMPLETED
        ]
    
    def get_observer_name(self) -> str:
        return "NotificationService"

class AnalyticsTracker(Observer):
    """Observer que recolecta analytics y métricas"""
    
    def __init__(self):
        self.metrics = {
            'total_users': 0,
            'total_games_played': 0,
            'total_classes_created': 0,
            'total_quizzes_created': 0,
            'daily_active_users': set(),
            'events_by_type': {}
        }
    
    async def update(self, event: Event) -> None:
        """Recolectar métricas del evento"""
        event_type_str = event.event_type.value
        
        # Contar eventos por tipo
        if event_type_str not in self.metrics['events_by_type']:
            self.metrics['events_by_type'][event_type_str] = 0
        self.metrics['events_by_type'][event_type_str] += 1
        
        # Métricas específicas
        if event.event_type == EventType.USER_REGISTERED:
            self.metrics['total_users'] += 1
        
        elif event.event_type == EventType.GAME_SESSION_STARTED:
            self.metrics['total_games_played'] += 1
        
        elif event.event_type == EventType.CLASS_CREATED:
            self.metrics['total_classes_created'] += 1
        
        elif event.event_type == EventType.QUIZ_CREATED:
            self.metrics['total_quizzes_created'] += 1
        
        # Usuario activo diario
        if event.user_id:
            today = datetime.now().strftime('%Y-%m-%d')
            self.metrics['daily_active_users'].add(f"{event.user_id}_{today}")
        
        print(f"📈 Métricas actualizadas: {event_type_str}")
    
    def get_interested_events(self) -> List[EventType]:
        return list(EventType)  # Interesado en todos los eventos
    
    def get_observer_name(self) -> str:
        return "AnalyticsTracker"
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Obtener resumen de métricas"""
        return {
            **self.metrics,
            'daily_active_users_count': len(self.metrics['daily_active_users'])
        }

# === INICIALIZADOR DEL SISTEMA ===

def initialize_observer_system():
    """Inicializar el sistema de observadores"""
    print("🚀 Inicializando sistema Observer Pattern...")
    
    event_manager = EventManager()
    
    # Crear y registrar observadores
    progress_tracker = ProgressTracker()
    achievement_system = AchievementSystem()
    notification_service = NotificationService()
    analytics_tracker = AnalyticsTracker()
    
    # Registrar observadores
    event_manager.attach(progress_tracker)
    event_manager.attach(achievement_system)
    event_manager.attach(notification_service)
    event_manager.attach(analytics_tracker)
    
    print(f"✅ Sistema Observer inicializado con {event_manager.get_observers_count()} observadores")
    
    return event_manager

# === EJEMPLO DE USO ===

async def demo_observer_pattern():
    """Demostración del patrón Observer"""
    print("\n🎯 === DEMO OBSERVER PATTERN ===")
    
    # Inicializar sistema
    event_manager = initialize_observer_system()
    
    # Simular eventos
    await event_manager.emit_event(
        EventType.USER_REGISTERED,
        {'email': 'usuario@test.com', 'name': 'Usuario Test'},
        user_id='user_123'
    )
    
    await event_manager.emit_event(
        EventType.STUDENT_JOINED_CLASS,
        {'class_id': 'class_456', 'class_name': 'Matemáticas 5to'},
        user_id='user_123'
    )
    
    await event_manager.emit_event(
        EventType.GAME_SESSION_COMPLETED,
        {'score': 100, 'total_questions': 10, 'time_taken': 120},
        user_id='user_123'
    )
    
    print(f"\n📊 Total eventos procesados: {len(event_manager.get_event_history())}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_observer_pattern())
