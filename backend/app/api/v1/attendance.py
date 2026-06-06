"""Attendance API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel
from datetime import date, timedelta
from typing import Optional

from app.core.database import get_db
from app.core.security import require_student, require_admin
from app.models.attendance import Attendance, AttendanceSummary, Subject

router = APIRouter()


# ─── Schemas ─────────────────────────────────────────────

class AttendanceMarkRequest(BaseModel):
    student_id: int
    subject_id: int
    date: date
    status: str  # present | absent | late | medical_leave | on_duty
    remarks: Optional[str] = None


# ─── Student Endpoints ────────────────────────────────────

@router.get("/my")
async def get_my_attendance(
    payload: dict = Depends(require_student),
    db: AsyncSession = Depends(get_db),
    academic_year: str = Query(default="2024-25"),
):
    """Get attendance summary for the logged-in student."""
    student_id = int(payload["sub"])

    result = await db.execute(
        select(AttendanceSummary, Subject)
        .join(Subject, AttendanceSummary.subject_id == Subject.id)
        .where(
            and_(
                AttendanceSummary.student_id == student_id,
                AttendanceSummary.academic_year == academic_year,
            )
        )
    )

    subjects = []
    total_classes_all = 0
    total_attended_all = 0

    for summary, subject in result.all():
        pct = summary.percentage
        required = 75.0
        deficit = 0
        classes_needed = 0

        if pct < required:
            # Calculate classes needed: solve (attended + x) / (total + x) >= 0.75
            if summary.total_classes > 0:
                attended = summary.attended_classes
                total = summary.total_classes
                # x = (0.75 * total - attended) / (1 - 0.75)
                x = (0.75 * total - attended) / 0.25
                classes_needed = max(0, int(x) + 1)
                deficit = round(required - pct, 2)

        total_classes_all += summary.total_classes
        total_attended_all += summary.attended_classes

        subjects.append({
            "subject_id": subject.id,
            "subject_code": subject.code,
            "subject_name": subject.name,
            "credits": subject.credits,
            "type": subject.type,
            "total_classes": summary.total_classes,
            "attended_classes": summary.attended_classes,
            "percentage": round(pct, 2),
            "status": "safe" if pct >= 75 else ("warning" if pct >= 65 else "critical"),
            "deficit": deficit,
            "classes_needed_for_75": classes_needed,
        })

    # Overall percentage
    overall_pct = (
        round((total_attended_all / total_classes_all) * 100, 2)
        if total_classes_all > 0
        else 0
    )

    return {
        "academic_year": academic_year,
        "overall": {
            "total_classes": total_classes_all,
            "attended_classes": total_attended_all,
            "percentage": overall_pct,
            "status": "safe" if overall_pct >= 75 else ("warning" if overall_pct >= 65 else "critical"),
        },
        "subjects": subjects,
    }


@router.get("/my/trend")
async def get_attendance_trend(
    payload: dict = Depends(require_student),
    db: AsyncSession = Depends(get_db),
    days: int = Query(default=30, ge=7, le=180),
):
    """Get daily attendance trend for the last N days."""
    student_id = int(payload["sub"])
    since = date.today() - timedelta(days=days)

    result = await db.execute(
        select(Attendance.date, func.count(Attendance.id).label("total"),
               func.sum((Attendance.status == "present").cast(int)).label("present"))
        .where(and_(Attendance.student_id == student_id, Attendance.date >= since))
        .group_by(Attendance.date)
        .order_by(Attendance.date)
    )

    trend = []
    for row in result.all():
        trend.append({
            "date": str(row.date),
            "total": row.total,
            "present": row.present or 0,
            "percentage": round(((row.present or 0) / row.total) * 100, 1) if row.total > 0 else 0,
        })

    return {"days": days, "trend": trend}


@router.get("/my/subject/{subject_id}")
async def get_subject_attendance(
    subject_id: int,
    payload: dict = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed attendance for a specific subject."""
    student_id = int(payload["sub"])

    result = await db.execute(
        select(Attendance)
        .where(and_(Attendance.student_id == student_id, Attendance.subject_id == subject_id))
        .order_by(Attendance.date.desc())
        .limit(60)
    )

    records = []
    for att in result.scalars().all():
        records.append({
            "date": str(att.date),
            "status": att.status,
            "remarks": att.remarks,
        })

    return {"subject_id": subject_id, "records": records}


# ─── Admin Endpoints ──────────────────────────────────────

@router.post("/mark", status_code=201)
async def mark_attendance(
    req: AttendanceMarkRequest,
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Mark attendance for a student (admin only)."""
    admin_id = int(payload["sub"])

    # Upsert attendance
    existing = await db.execute(
        select(Attendance).where(
            and_(
                Attendance.student_id == req.student_id,
                Attendance.subject_id == req.subject_id,
                Attendance.date == req.date,
            )
        )
    )
    att = existing.scalar_one_or_none()

    if att:
        att.status = req.status
        att.remarks = req.remarks
        att.marked_by = admin_id
    else:
        att = Attendance(
            student_id=req.student_id,
            subject_id=req.subject_id,
            date=req.date,
            status=req.status,
            remarks=req.remarks,
            marked_by=admin_id,
        )
        db.add(att)

    await db.flush()

    # Update summary
    await _update_attendance_summary(db, req.student_id, req.subject_id)
    await db.commit()

    return {"message": "Attendance marked successfully"}


async def _update_attendance_summary(db: AsyncSession, student_id: int, subject_id: int):
    """Recalculate and update attendance summary."""
    # Get current academic year (simplified)
    academic_year = "2024-25"

    counts = await db.execute(
        select(
            func.count(Attendance.id).label("total"),
            func.sum((Attendance.status.in_(["present", "late", "on_duty"])).cast(int)).label("attended"),
        )
        .where(and_(Attendance.student_id == student_id, Attendance.subject_id == subject_id))
    )
    row = counts.one()

    # Get subject semester
    sub = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = sub.scalar_one_or_none()
    semester = subject.semester if subject else 1

    # Upsert summary
    existing = await db.execute(
        select(AttendanceSummary).where(
            and_(
                AttendanceSummary.student_id == student_id,
                AttendanceSummary.subject_id == subject_id,
                AttendanceSummary.academic_year == academic_year,
            )
        )
    )
    summary = existing.scalar_one_or_none()

    if summary:
        summary.total_classes = row.total or 0
        summary.attended_classes = row.attended or 0
    else:
        summary = AttendanceSummary(
            student_id=student_id,
            subject_id=subject_id,
            academic_year=academic_year,
            semester=semester,
            total_classes=row.total or 0,
            attended_classes=row.attended or 0,
        )
        db.add(summary)


@router.get("/admin/stats")
async def get_attendance_stats(
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    academic_year: str = Query(default="2024-25"),
):
    """Get overall attendance statistics (admin only)."""
    result = await db.execute(
        select(
            func.count(AttendanceSummary.student_id.distinct()).label("total_students"),
            func.avg(
                (AttendanceSummary.attended_classes / AttendanceSummary.total_classes) * 100
            ).label("avg_percentage"),
            func.sum(
                (
                    (AttendanceSummary.attended_classes / AttendanceSummary.total_classes) * 100 < 75
                ).cast(int)
            ).label("below_75"),
        )
        .where(
            and_(
                AttendanceSummary.academic_year == academic_year,
                AttendanceSummary.total_classes > 0,
            )
        )
    )
    row = result.one()

    return {
        "academic_year": academic_year,
        "total_students": row.total_students or 0,
        "average_percentage": round(float(row.avg_percentage or 0), 2),
        "students_below_75": row.below_75 or 0,
    }
