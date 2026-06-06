"""Student management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.core.database import get_db
from app.core.security import require_student, require_admin, hash_password
from app.models.student import Student

router = APIRouter()


class CreateStudentRequest(BaseModel):
    student_id: str
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    course: str
    branch: Optional[str] = None
    semester: int = 1
    year: int = 1
    batch: int
    section: Optional[str] = None
    category: str = "general"
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    is_hostel_student: bool = False


class UpdateStudentRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    address: Optional[str] = None
    avatar_url: Optional[str] = None


@router.get("/")
async def list_students(
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    course: Optional[str] = None,
    semester: Optional[int] = None,
    search: Optional[str] = None,
):
    """List students with pagination (admin only)."""
    query = select(Student).where(Student.is_active == True)

    if course:
        query = query.where(Student.course == course)
    if semester:
        query = query.where(Student.semester == semester)
    if search:
        query = query.where(
            Student.name.ilike(f"%{search}%") | Student.student_id.ilike(f"%{search}%")
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginate
    query = query.offset((page - 1) * limit).limit(limit).order_by(Student.name)
    result = await db.execute(query)
    students = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "students": [
            {
                "id": s.id,
                "student_id": s.student_id,
                "name": s.name,
                "email": s.email,
                "phone": s.phone,
                "course": s.course,
                "semester": s.semester,
                "batch": s.batch,
                "category": s.category,
                "is_hostel_student": s.is_hostel_student,
            }
            for s in students
        ],
    }


@router.post("/", status_code=201)
async def create_student(
    req: CreateStudentRequest,
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new student (admin only)."""
    # Check for duplicate email or student_id
    existing = await db.execute(
        select(Student).where(
            (Student.email == req.email) | (Student.student_id == req.student_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Student with this email or ID already exists")

    student = Student(
        student_id=req.student_id,
        name=req.name,
        email=req.email,
        password_hash=hash_password(req.password),
        phone=req.phone,
        course=req.course,
        branch=req.branch,
        semester=req.semester,
        year=req.year,
        batch=req.batch,
        section=req.section,
        category=req.category,
        guardian_name=req.guardian_name,
        guardian_phone=req.guardian_phone,
        is_hostel_student=req.is_hostel_student,
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)

    return {"message": "Student created", "student_id": student.student_id, "id": student.id}


@router.get("/{student_id_or_int}")
async def get_student(
    student_id_or_int: str,
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get student by internal ID or student_id string."""
    if student_id_or_int.isdigit():
        query = select(Student).where(Student.id == int(student_id_or_int))
    else:
        query = select(Student).where(Student.student_id == student_id_or_int)

    result = await db.execute(query)
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return {
        "id": student.id,
        "student_id": student.student_id,
        "name": student.name,
        "email": student.email,
        "phone": student.phone,
        "date_of_birth": str(student.date_of_birth) if student.date_of_birth else None,
        "gender": student.gender,
        "course": student.course,
        "branch": student.branch,
        "semester": student.semester,
        "year": student.year,
        "batch": student.batch,
        "section": student.section,
        "category": student.category,
        "guardian_name": student.guardian_name,
        "guardian_phone": student.guardian_phone,
        "is_hostel_student": student.is_hostel_student,
        "is_active": student.is_active,
        "created_at": str(student.created_at),
    }


@router.put("/me")
async def update_my_profile(
    req: UpdateStudentRequest,
    payload: dict = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Update logged-in student's profile."""
    student_id = int(payload["sub"])
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(student, field, value)

    await db.commit()
    return {"message": "Profile updated"}
