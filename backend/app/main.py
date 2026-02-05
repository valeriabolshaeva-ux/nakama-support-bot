"""
FastAPI Application Entry Point.

This module creates and configures the FastAPI application instance.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.
    
    Manages startup and shutdown events for the application.
    Use this for database connections, background tasks initialization, etc.
    """
    # === STARTUP ===
    # TODO: Initialize database connection pool
    # TODO: Initialize Redis connection
    # TODO: Start background tasks
    print(f"🚀 Starting {settings.app_name} in {settings.environment} mode")
    
    yield
    
    # === SHUTDOWN ===
    # TODO: Close database connections
    # TODO: Close Redis connections
    # TODO: Stop background tasks
    print(f"👋 Shutting down {settings.app_name}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Universal project template with FastAPI backend",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/api/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

# === CORS Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Health Check ===
@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """
    Health check endpoint.
    
    Returns:
        dict: Health status of the application.
    """
    return {
        "status": "healthy",
        "environment": settings.environment,
        "debug": settings.debug,
    }


# === API Routers ===
# TODO: Include API routers here
# from app.api.v1 import auth, users
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
# app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])


@app.get("/", tags=["Root"])
async def root() -> dict:
    """
    Root endpoint.
    
    Returns:
        dict: Welcome message and API information.
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs" if settings.debug else "Disabled in production",
        "health": "/health",
    }
