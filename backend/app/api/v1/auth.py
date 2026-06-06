"""Authentication endpoints for students and admins."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    require_student,
    require_admin,
)
from app.models.student import Student

router = APIRouter()


# ─── Schemas ─────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    user_type: str = "student"  # "student" | "admin"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_type: str
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ─── Endpoints ───────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login for students and admins."""
    if req.user_type == "student":
        result = await db.execute(select(Student).where(Student.email == req.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(req.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is deactivated")

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        await db.commit()

        access_token = create_access_token(str(user.id), "student")
        refresh_token = create_refresh_token(str(user.id), "student")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user_type="student",
            user={
                "id": user.id,
                "student_id": user.student_id,
                "name": user.name,
                "email": user.email,
                "course": user.course,
                "semester": user.semester,
                "avatar_url": user.avatar_url,
            },
        )

    elif req.user_type == "admin":
        # Import Admin model lazily to avoid circular imports
        from app.models.admin import Admin
        result = await db.execute(select(Admin).where(Admin.email == req.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(req.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is deactivated")

        user.last_login = datetime.now(timezone.utc)
        await db.commit()

        access_token = create_access_token(str(user.id), "admin")
        refresh_token = create_refresh_token(str(user.id), "admin")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user_type="admin",
            user={
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "department": user.department,
            },
        )

    raise HTTPException(status_code=400, detail="Invalid user_type. Use 'student' or 'admin'")


@router.post("/refresh", response_model=dict)
async def refresh_token(req: RefreshRequest):
    """Refresh access token using refresh token."""
    payload = decode_token(req.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = create_access_token(payload["sub"], payload["user_type"])
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(payload: dict = Depends(require_student)):
    """Logout (client should discard the token)."""
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(payload: dict = Depends(require_student), db: AsyncSession = Depends(get_db)):
    """Get current student profile."""
    student_id = int(payload["sub"])
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return {
        "id": student.id,
        "student_id": student.student_id,
        "name": student.name,
        "email": student.email,
        "phone": student.phone,
        "course": student.course,
        "branch": student.branch,
        "semester": student.semester,
        "year": student.year,
        "batch": student.batch,
        "section": student.section,
        "category": student.category,
        "avatar_url": student.avatar_url,
        "is_hostel_student": student.is_hostel_student,
        "guardian_name": student.guardian_name,
    }


@router.put("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    payload: dict = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Change student password."""
    student_id = int(payload["sub"])
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if not verify_password(req.current_password, student.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    student.password_hash = hash_password(req.new_password)
    await db.commit()

    return {"message": "Password changed successfully"}
