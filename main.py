from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn

# Import routers
from routers import auth, users, classes, games, content, progress
from database.connection import engine, Base
from core.config import settings, ALLOWED_ORIGINS

# Security scheme
security = HTTPBearer()

# Create database tables
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup on shutdown
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

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(classes.router, prefix="/classes", tags=["classes"])
app.include_router(games.router, prefix="/games", tags=["games"])
app.include_router(content.router, prefix="/content", tags=["content"])
app.include_router(progress.router, prefix="/progress", tags=["progress"])

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
