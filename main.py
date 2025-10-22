"""
Main FastAPI application for Ludix App AI Server.

This application implements several design patterns:
- Factory Pattern: Database session creation (db/base.py)
- Observer Pattern: Progress tracking through quiz attempts (models)
- Decorator Pattern: Authentication decorators (services/AuthService.py)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.base import engine, Base
from routers import auth

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI(
    title="Ludix App AI Server",
    description="Backend API for Ludix educational quiz application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)


@app.get("/")
def read_root():
    """Root endpoint - API health check."""
    return {
        "message": "Welcome to Ludix App AI Server",
        "status": "active",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "ludix-app-ai-server"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
