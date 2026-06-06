"""Hostel management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import secrets

from app.core.database import get_db
from app.core.security import require_student, require_admin
from app.models.hostel import Hostel, HostelAllocation, HostelPayment

router = APIRouter()


@router.get("/my")
async def get_my_hostel(
    payload: dict = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Get hostel details for the logged-in student."""
    student_id = int(payload["sub"])

    result = await db.execute(
        select(HostelAllocation, Hostel)
        .join(Hostel, HostelAllocation.hostel_id == Hostel.id)
        .where(
            and_(
                HostelAllocation.student_id == student_id,
                HostelAllocation.status == "active",
            )
        )
    )
    row = result.first()

    if not row:
        return {"has_hostel": False, "message": "You are not allocated a hostel room"}

    alloc, room = row

    # Get payment history
    pay_result = await db.execute(
        select(HostelPayment)
        .where(HostelPayment.allocation_id == alloc.id)
        .order_by(HostelPayment.payment_date.desc())
        .limit(12)
    )
    payments = pay_result.scalars().all()

    last_payment = payments[0] if payments else None

    return {
        "has_hostel": True,
        "hostel": {
            "hostel_name": room.hostel_name,
            "block": room.block,
            "room_number": room.room_number,
            "floor": room.floor,
            "room_type": room.room_type,
            "monthly_rent": float(room.monthly_rent),
            "amenities": room.amenities,
        },
        "allocation": {
            "id": alloc.id,
            "allotment_date": str(alloc.allotment_date),
            "academic_year": alloc.academic_year,
            "total_fee": float(alloc.total_fee),
            "paid_amount": float(alloc.paid_amount),
            "remaining_fee": alloc.remaining_fee,
            "next_due_date": str(alloc.next_due_date) if alloc.next_due_date else None,
            "status": alloc.status,
            "fine_status": "clear",  # Could check fines table
        },
        "last_payment": {
            "amount": float(last_payment.amount),
            "payment_date": str(last_payment.payment_date),
            "receipt_number": last_payment.receipt_number,
            "month_year": last_payment.month_year,
        } if last_payment else None,
        "payment_history": [
            {
                "amount": float(p.amount),
                "payment_date": str(p.payment_date),
                "receipt_number": p.receipt_number,
                "payment_method": p.payment_method,
                "month_year": p.month_year,
            }
            for p in payments
        ],
    }


@router.get("/rooms")
async def list_available_rooms(
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all hostel rooms with availability status (admin)."""
    result = await db.execute(select(Hostel).order_by(Hostel.hostel_name, Hostel.room_number))
    rooms = result.scalars().all()

    return {
        "rooms": [
            {
                "id": r.id,
                "hostel_name": r.hostel_name,
                "block": r.block,
                "room_number": r.room_number,
                "room_type": r.room_type,
                "capacity": r.capacity,
                "monthly_rent": float(r.monthly_rent),
                "is_available": r.is_available,
            }
            for r in rooms
        ]
    }


class HostelPaymentRequest(BaseModel):
    allocation_id: int
    amount: float
    payment_method: str
    transaction_id: Optional[str] = None
    month_year: str  # e.g., "2024-12"
    remarks: Optional[str] = None


@router.post("/payment", status_code=201)
async def record_hostel_payment(
    req: HostelPaymentRequest,
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Record hostel fee payment (admin only)."""
    alloc_result = await db.execute(
        select(HostelAllocation).where(HostelAllocation.id == req.allocation_id)
    )
    alloc = alloc_result.scalar_one_or_none()

    if not alloc:
        raise HTTPException(status_code=404, detail="Allocation not found")

    receipt = f"HRCP{datetime.now().strftime('%Y%m%d')}{secrets.token_hex(3).upper()}"

    payment = HostelPayment(
        allocation_id=req.allocation_id,
        student_id=alloc.student_id,
        amount=req.amount,
        payment_date=datetime.utcnow(),
        payment_method=req.payment_method,
        transaction_id=req.transaction_id,
        receipt_number=receipt,
        month_year=req.month_year,
        remarks=req.remarks,
    )
    db.add(payment)

    alloc.paid_amount = float(alloc.paid_amount) + req.amount
    await db.commit()

    return {"message": "Hostel payment recorded", "receipt_number": receipt}


@router.get("/admin/stats")
async def get_hostel_stats(
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Hostel occupancy and payment statistics."""
    from sqlalchemy import func

    total_rooms = (await db.execute(select(func.count(Hostel.id)))).scalar()
    occupied = (await db.execute(
        select(func.count(HostelAllocation.id))
        .where(HostelAllocation.status == "active")
    )).scalar()

    return {
        "total_rooms": total_rooms,
        "occupied_rooms": occupied,
        "available_rooms": total_rooms - occupied,
        "occupancy_rate": round((occupied / total_rooms) * 100, 1) if total_rooms > 0 else 0,
    }
