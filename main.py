from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# Import routers (Supabase version)
from routers import (
    auth_supabase as auth, 
    users_supabase as users, 
    games_supabase as games,
    classes_supabase as classes,
    quizzes_supabase as quizzes
)
from core.config import settings, ALLOWED_ORIGINS
from services.supabase_service import supabase_service

# Security scheme se maneja en cada router

# App startup/shutdown with Supabase only
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Supabase connection on startup
    print("🚀 Iniciando Ludix API con Supabase...")
    try:
        # Test Supabase connection
        client = supabase_service.client
        print("✅ Conexión con Supabase establecida")
        
        # Inicializar sistema Observer Pattern
        from patterns.observer_system import initialize_observer_system
        event_manager = initialize_observer_system()
        print("✅ Sistema Observer Pattern inicializado")
        
    except Exception as e:
        print(f"⚠️ Error conectando con Supabase: {e}")
        
    yield
    
    # Cleanup on shutdown
    print("🔄 Cerrando Ludix API...")
    pass

# FastAPI instance with lifespan
app = FastAPI(
    title="Ludix API Server",
    description="Backend API para la plataforma educativa Ludix",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Include routers (usando solo Supabase)
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(classes.router, prefix="/classes", tags=["classes"])
app.include_router(quizzes.router, prefix="/quizzes", tags=["quizzes"])
app.include_router(games.router, prefix="/games", tags=["games"])

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Ludix API Server",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ludix-api"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )
