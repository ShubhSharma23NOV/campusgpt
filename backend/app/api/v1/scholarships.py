"""Scholarship management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.core.security import require_student, require_admin
from app.models.scholarship import Scholarship, ScholarshipApplication, ScholarshipPayment
from app.models.student import Student
from app.models.attendance import AttendanceSummary

router = APIRouter()


@router.get("/")
async def list_scholarships(
    db: AsyncSession = Depends(get_db),
    academic_year: str = "2024-25",
):
    """List all active scholarships."""
    result = await db.execute(
        select(Scholarship).where(
            and_(Scholarship.is_active == True, Scholarship.academic_year == academic_year)
        )
    )
    scholarships = result.scalars().all()

    today = date.today()
    return {
        "scholarships": [
            {
                "id": s.id,
                "name": s.name,
                "type": s.type,
                "amount": float(s.amount),
                "eligibility_criteria": s.eligibility_criteria,
                "application_start": str(s.application_start) if s.application_start else None,
                "application_end": str(s.application_end) if s.application_end else None,
                "is_open": (
                    s.application_start <= today <= s.application_end
                    if s.application_start and s.application_end
                    else False
                ),
                "description": s.description,
                "min_attendance": float(s.min_attendance) if s.min_attendance else None,
                "min_percentage": float(s.min_percentage) if s.min_percentage else None,
                "categories_eligible": s.categories_eligible,
            }
            for s in scholarships
        ]
    }


@router.get("/my")
async def get_my_scholarships(
    payload: dict = Depends(require_student),
    db: AsyncSession = Depends(get_db),
    academic_year: str = "2024-25",
):
    """Get scholarship applications for the logged-in student."""
    student_id = int(payload["sub"])

    result = await db.execute(
        select(ScholarshipApplication, Scholarship)
        .join(Scholarship, ScholarshipApplication.scholarship_id == Scholarship.id)
        .where(ScholarshipApplication.student_id == student_id)
    )
    applications = []
    total_received = 0.0

    for app, sch in result.all():
        approved = float(app.approved_amount) if app.approved_amount else 0
        if app.status == "disbursed":
            total_received += approved

        applications.append({
            "application_id": app.id,
            "scholarship_id": sch.id,
            "scholarship_name": sch.name,
            "scholarship_type": sch.type,
            "requested_amount": float(sch.amount),
            "approved_amount": float(app.approved_amount) if app.approved_amount else None,
            "status": app.status,
            "applied_date": str(app.applied_date),
            "approval_date": str(app.approval_date) if app.approval_date else None,
            "remarks": app.remarks,
        })

    # Determine eligible scholarships not yet applied for
    eligible = await _check_eligibility(student_id, academic_year, db)

    return {
        "applications": applications,
        "total_received": total_received,
        "eligible_scholarships": eligible,
    }


async def _check_eligibility(student_id: int, academic_year: str, db: AsyncSession) -> list:
    """Check which scholarships a student is eligible for."""
    student_result = await db.execute(select(Student).where(Student.id == student_id))
    student = student_result.scalar_one_or_none()
    if not student:
        return []

    # Get overall attendance percentage
    att_result = await db.execute(
        select(AttendanceSummary)
        .where(
            and_(
                AttendanceSummary.student_id == student_id,
                AttendanceSummary.academic_year == academic_year,
            )
        )
    )
    summaries = att_result.scalars().all()
    overall_pct = 0.0
    if summaries:
        total_t = sum(s.total_classes for s in summaries)
        total_a = sum(s.attended_classes for s in summaries)
        overall_pct = (total_a / total_t) * 100 if total_t > 0 else 0.0

    # Get all scholarships
    sch_result = await db.execute(
        select(Scholarship).where(
            and_(Scholarship.is_active == True, Scholarship.academic_year == academic_year)
        )
    )
    all_scholarships = sch_result.scalars().all()

    # Already applied
    applied_result = await db.execute(
        select(ScholarshipApplication.scholarship_id)
        .where(ScholarshipApplication.student_id == student_id)
    )
    applied_ids = {r[0] for r in applied_result.all()}

    eligible = []
    today = date.today()
    for sch in all_scholarships:
        if sch.id in applied_ids:
            continue

        # Check attendance
        if sch.min_attendance and overall_pct < float(sch.min_attendance):
            continue

        # Check category
        if sch.categories_eligible:
            if student.category not in sch.categories_eligible:
                continue

        # Check if open
        is_open = (
            sch.application_start <= today <= sch.application_end
            if sch.application_start and sch.application_end
            else False
        )

        eligible.append({
            "id": sch.id,
            "name": sch.name,
            "type": sch.type,
            "amount": float(sch.amount),
            "deadline": str(sch.application_end) if sch.application_end else None,
            "is_open": is_open,
        })

    return eligible


@router.post("/apply/{scholarship_id}", status_code=201)
async def apply_for_scholarship(
    scholarship_id: int,
    payload: dict = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Apply for a scholarship."""
    student_id = int(payload["sub"])

    sch_result = await db.execute(select(Scholarship).where(Scholarship.id == scholarship_id))
    scholarship = sch_result.scalar_one_or_none()

    if not scholarship or not scholarship.is_active:
        raise HTTPException(status_code=404, detail="Scholarship not found or inactive")

    # Check if already applied
    existing = await db.execute(
        select(ScholarshipApplication).where(
            and_(
                ScholarshipApplication.student_id == student_id,
                ScholarshipApplication.scholarship_id == scholarship_id,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You have already applied for this scholarship")

    application = ScholarshipApplication(
        student_id=student_id,
        scholarship_id=scholarship_id,
        status="submitted",
    )
    db.add(application)
    await db.commit()

    return {"message": "Application submitted successfully", "application_id": application.id}
