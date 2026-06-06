"""
CampusGPT – Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import (
    auth,
    students,
    attendance,
    fees,
    hostel,
    scholarships,
    fines,
    notifications,
    ai_chat,
    policies,
    admin,
    voice,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "policies"), exist_ok=True)
    os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
    print(f"🚀 CampusGPT API starting on port 8000")
    yield
    # Shutdown
    print("CampusGPT API shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Student Copilot Platform",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# API routers
PREFIX = "/api/v1"
app.include_router(auth.router,         prefix=f"{PREFIX}/auth",         tags=["Authentication"])
app.include_router(students.router,     prefix=f"{PREFIX}/students",     tags=["Students"])
app.include_router(attendance.router,   prefix=f"{PREFIX}/attendance",   tags=["Attendance"])
app.include_router(fees.router,         prefix=f"{PREFIX}/fees",         tags=["Fees"])
app.include_router(hostel.router,       prefix=f"{PREFIX}/hostel",       tags=["Hostel"])
app.include_router(scholarships.router, prefix=f"{PREFIX}/scholarships", tags=["Scholarships"])
app.include_router(fines.router,        prefix=f"{PREFIX}/fines",        tags=["Fines"])
app.include_router(notifications.router,prefix=f"{PREFIX}/notifications",tags=["Notifications"])
app.include_router(ai_chat.router,      prefix=f"{PREFIX}/ai",           tags=["AI Assistant"])
app.include_router(policies.router,     prefix=f"{PREFIX}/policies",     tags=["Policies"])
app.include_router(admin.router,        prefix=f"{PREFIX}/admin",        tags=["Admin"])
app.include_router(voice.router,        prefix=f"{PREFIX}/voice",        tags=["Voice"])


@app.get("/", tags=["Health"])
async def root():
    return {"message": "CampusGPT API is running", "version": settings.APP_VERSION}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME}
