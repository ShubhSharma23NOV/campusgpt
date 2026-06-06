"""Admin analytics and management endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.security import require_admin
from app.models.student import Student
from app.models.attendance import AttendanceSummary
from app.models.fees import Fee, FeePayment
from app.models.hostel import HostelAllocation
from app.models.scholarship import ScholarshipApplication
from app.models.fine import Fine

router = APIRouter()


@router.get("/dashboard")
async def admin_dashboard(
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    academic_year: str = "2024-25",
):
    """Get comprehensive admin dashboard statistics."""

    # Student stats
    total_students = (await db.execute(
        select(func.count(Student.id)).where(Student.is_active == True)
    )).scalar() or 0

    hostel_students = (await db.execute(
        select(func.count(Student.id)).where(
            and_(Student.is_active == True, Student.is_hostel_student == True)
        )
    )).scalar() or 0

    # Attendance stats
    att_result = (await db.execute(
        select(
            func.avg(
                func.IF(
                    AttendanceSummary.total_classes > 0,
                    (AttendanceSummary.attended_classes / AttendanceSummary.total_classes) * 100,
                    0,
                )
            ).label("avg"),
            func.sum(
                func.IF(
                    AttendanceSummary.total_classes > 0,
                    func.IF(
                        (AttendanceSummary.attended_classes / AttendanceSummary.total_classes) * 100 < 75,
                        1,
                        0,
                    ),
                    0,
                )
            ).label("below_75"),
        )
        .where(AttendanceSummary.academic_year == academic_year)
    )).one()

    # Fee stats
    fee_result = (await db.execute(
        select(
            func.sum(Fee.total_amount).label("total"),
            func.sum(Fee.paid_amount).label("paid"),
        )
        .where(Fee.academic_year == academic_year)
    )).one()

    # Hostel occupancy
    active_allocations = (await db.execute(
        select(func.count(HostelAllocation.id))
        .where(HostelAllocation.status == "active")
    )).scalar() or 0

    # Scholarships
    scholarship_stats = (await db.execute(
        select(
            ScholarshipApplication.status,
            func.count(ScholarshipApplication.id).label("count"),
        )
        .group_by(ScholarshipApplication.status)
    )).all()

    sch_dict = {row.status: row.count for row in scholarship_stats}

    # Fines
    fine_stats = (await db.execute(
        select(
            func.sum(Fine.amount).label("total"),
            func.sum(Fine.paid_amount).label("paid"),
            func.count(Fine.id).label("count"),
        )
    )).one()

    total_fees = float(fee_result.total or 0)
    paid_fees = float(fee_result.paid or 0)

    return {
        "students": {
            "total": total_students,
            "hostel": hostel_students,
            "day_scholars": total_students - hostel_students,
        },
        "attendance": {
            "average_percentage": round(float(att_result.avg or 0), 2),
            "students_below_75": int(att_result.below_75 or 0),
        },
        "fees": {
            "total_billed": total_fees,
            "total_collected": paid_fees,
            "pending": round(total_fees - paid_fees, 2),
            "collection_rate": round((paid_fees / total_fees) * 100, 2) if total_fees > 0 else 0,
        },
        "hostel": {
            "occupied_rooms": active_allocations,
        },
        "scholarships": {
            "submitted": sch_dict.get("submitted", 0),
            "approved": sch_dict.get("approved", 0),
            "disbursed": sch_dict.get("disbursed", 0),
            "rejected": sch_dict.get("rejected", 0),
        },
        "fines": {
            "total_amount": float(fine_stats.total or 0),
            "collected": float(fine_stats.paid or 0),
            "total_count": int(fine_stats.count or 0),
        },
    }


@router.get("/analytics/attendance-distribution")
async def attendance_distribution(
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    academic_year: str = "2024-25",
):
    """Distribution of attendance percentages across students."""
    result = await db.execute(
        select(
            Student.course,
            func.avg(
                func.IF(
                    AttendanceSummary.total_classes > 0,
                    (AttendanceSummary.attended_classes / AttendanceSummary.total_classes) * 100,
                    0,
                )
            ).label("avg_attendance"),
        )
        .join(AttendanceSummary, Student.id == AttendanceSummary.student_id)
        .where(AttendanceSummary.academic_year == academic_year)
        .group_by(Student.course)
    )

    return {
        "by_course": [
            {"course": row.course, "average": round(float(row.avg_attendance or 0), 2)}
            for row in result.all()
        ]
    }


@router.get("/analytics/fee-collection")
async def fee_collection_trend(
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Monthly fee collection trend."""
    result = await db.execute(
        select(
            func.date_format(FeePayment.payment_date, "%Y-%m").label("month"),
            func.sum(FeePayment.amount).label("amount"),
            func.count(FeePayment.id).label("transactions"),
        )
        .group_by(func.date_format(FeePayment.payment_date, "%Y-%m"))
        .order_by(func.date_format(FeePayment.payment_date, "%Y-%m").desc())
        .limit(12)
    )

    return {
        "monthly_trend": [
            {
                "month": row.month,
                "amount": float(row.amount or 0),
                "transactions": row.transactions,
            }
            for row in result.all()
        ]
    }
