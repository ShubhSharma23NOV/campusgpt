"""Fine management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
import secrets

from app.core.database import get_db
from app.core.security import require_student, require_admin
from app.models.fine import Fine, FinePayment

router = APIRouter()


class CreateFineRequest(BaseModel):
    student_id: int
    fine_type: str
    reason: str
    amount: float
    fine_date: date
    due_date: Optional[date] = None
    remarks: Optional[str] = None


class FinePaymentRequest(BaseModel):
    fine_id: int
    amount: float
    payment_method: str
    transaction_id: Optional[str] = None


@router.get("/my")
async def get_my_fines(
    payload: dict = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Get all fines for the logged-in student."""
    student_id = int(payload["sub"])

    result = await db.execute(
        select(Fine)
        .where(Fine.student_id == student_id)
        .order_by(Fine.fine_date.desc())
    )
    fines = result.scalars().all()

    total_fine = sum(float(f.amount) for f in fines)
    total_paid = sum(float(f.paid_amount) for f in fines)
    total_pending = total_fine - total_paid

    fine_list = []
    for fine in fines:
        # Get payments for this fine
        pay_result = await db.execute(
            select(FinePayment).where(FinePayment.fine_id == fine.id).order_by(FinePayment.payment_date.desc())
        )
        payments = pay_result.scalars().all()

        fine_list.append({
            "id": fine.id,
            "fine_type": fine.fine_type,
            "reason": fine.reason,
            "amount": float(fine.amount),
            "paid_amount": float(fine.paid_amount),
            "remaining_amount": fine.remaining_amount,
            "fine_date": str(fine.fine_date),
            "due_date": str(fine.due_date) if fine.due_date else None,
            "status": fine.status,
            "is_overdue": (
                fine.due_date and fine.due_date < date.today() and fine.status != "paid"
            ),
            "payments": [
                {
                    "amount": float(p.amount),
                    "payment_date": str(p.payment_date),
                    "payment_method": p.payment_method,
                    "receipt_number": p.receipt_number,
                }
                for p in payments
            ],
        })

    return {
        "summary": {
            "total_fines": len(fines),
            "total_amount": round(total_fine, 2),
            "total_paid": round(total_paid, 2),
            "total_pending": round(total_pending, 2),
            "has_pending": total_pending > 0,
        },
        "fines": fine_list,
    }


@router.post("/", status_code=201)
async def create_fine(
    req: CreateFineRequest,
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a fine for a student (admin only)."""
    fine = Fine(
        student_id=req.student_id,
        fine_type=req.fine_type,
        reason=req.reason,
        amount=req.amount,
        fine_date=req.fine_date,
        due_date=req.due_date,
        imposed_by=int(payload["sub"]),
        remarks=req.remarks,
    )
    db.add(fine)
    await db.commit()

    return {"message": "Fine created", "fine_id": fine.id}


@router.post("/pay", status_code=201)
async def pay_fine(
    req: FinePaymentRequest,
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Record fine payment (admin only)."""
    fine_result = await db.execute(select(Fine).where(Fine.id == req.fine_id))
    fine = fine_result.scalar_one_or_none()

    if not fine:
        raise HTTPException(status_code=404, detail="Fine not found")

    if req.amount > fine.remaining_amount:
        raise HTTPException(status_code=400, detail=f"Amount exceeds remaining balance of ₹{fine.remaining_amount}")

    receipt = f"FRCP{datetime.now().strftime('%Y%m%d')}{secrets.token_hex(3).upper()}"

    payment = FinePayment(
        fine_id=req.fine_id,
        student_id=fine.student_id,
        amount=req.amount,
        payment_date=datetime.utcnow(),
        payment_method=req.payment_method,
        transaction_id=req.transaction_id,
        receipt_number=receipt,
    )
    db.add(payment)

    fine.paid_amount = float(fine.paid_amount) + req.amount
    await db.commit()

    return {"message": "Fine payment recorded", "receipt_number": receipt}


@router.get("/admin/all")
async def get_all_fines(
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get all fines (admin only)."""
    from sqlalchemy import func
    result = await db.execute(
        select(Fine).order_by(Fine.fine_date.desc()).limit(100)
    )
    fines = result.scalars().all()

    return {
        "fines": [
            {
                "id": f.id,
                "student_id": f.student_id,
                "fine_type": f.fine_type,
                "reason": f.reason,
                "amount": float(f.amount),
                "paid_amount": float(f.paid_amount),
                "status": f.status,
                "fine_date": str(f.fine_date),
                "due_date": str(f.due_date) if f.due_date else None,
            }
            for f in fines
        ]
    }
