"""Fee management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.core.security import require_student, require_admin
from app.models.fees import Fee, FeePayment

router = APIRouter()


class PaymentRequest(BaseModel):
    fee_id: int
    amount: float
    payment_method: str
    transaction_id: Optional[str] = None
    installment_number: Optional[int] = None
    remarks: Optional[str] = None


@router.get("/my")
async def get_my_fees(
    payload: dict = Depends(require_student),
    db: AsyncSession = Depends(get_db),
    academic_year: str = Query(default="2024-25"),
):
    """Get fee details for the logged-in student."""
    student_id = int(payload["sub"])

    result = await db.execute(
        select(Fee)
        .where(and_(Fee.student_id == student_id, Fee.academic_year == academic_year))
    )
    fees = result.scalars().all()

    fee_list = []
    total_paid = 0
    total_remaining = 0
    total_amount = 0

    for fee in fees:
        net = fee.net_amount
        remaining = fee.remaining_amount
        total_amount += net
        total_paid += float(fee.paid_amount)
        total_remaining += remaining

        # Get payments
        pay_result = await db.execute(
            select(FeePayment)
            .where(FeePayment.fee_id == fee.id)
            .order_by(FeePayment.payment_date.desc())
        )
        payments = pay_result.scalars().all()

        fee_list.append({
            "id": fee.id,
            "fee_type": fee.fee_type,
            "total_amount": float(fee.total_amount),
            "discount_amount": float(fee.discount_amount),
            "waiver_amount": float(fee.waiver_amount),
            "net_amount": net,
            "paid_amount": float(fee.paid_amount),
            "remaining_amount": remaining,
            "due_date": str(fee.due_date) if fee.due_date else None,
            "status": fee.status,
            "payments": [
                {
                    "id": p.id,
                    "amount": float(p.amount),
                    "payment_date": str(p.payment_date),
                    "payment_method": p.payment_method,
                    "receipt_number": p.receipt_number,
                    "installment_number": p.installment_number,
                }
                for p in payments
            ],
        })

    # Calculate installments
    total_installments = 2  # Assume bi-annual
    paid_installments = sum(
        1 for f in fees if f.status in ("paid",)
    )

    return {
        "academic_year": academic_year,
        "summary": {
            "total_amount": round(total_amount, 2),
            "total_paid": round(total_paid, 2),
            "total_remaining": round(total_remaining, 2),
            "total_installments": total_installments,
            "installments_paid": paid_installments,
            "installments_remaining": total_installments - paid_installments,
        },
        "fees": fee_list,
    }


@router.get("/my/history")
async def get_payment_history(
    payload: dict = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Get complete payment history."""
    student_id = int(payload["sub"])

    result = await db.execute(
        select(FeePayment, Fee)
        .join(Fee, FeePayment.fee_id == Fee.id)
        .where(FeePayment.student_id == student_id)
        .order_by(FeePayment.payment_date.desc())
        .limit(50)
    )

    history = []
    for payment, fee in result.all():
        history.append({
            "id": payment.id,
            "fee_type": fee.fee_type,
            "amount": float(payment.amount),
            "payment_date": str(payment.payment_date),
            "payment_method": payment.payment_method,
            "transaction_id": payment.transaction_id,
            "receipt_number": payment.receipt_number,
        })

    return {"history": history}


@router.post("/pay", status_code=201)
async def record_payment(
    req: PaymentRequest,
    payload: dict = Depends(require_admin),  # Only admin can record payments
    db: AsyncSession = Depends(get_db),
):
    """Record a fee payment (admin only)."""
    import secrets

    fee_result = await db.execute(select(Fee).where(Fee.id == req.fee_id))
    fee = fee_result.scalar_one_or_none()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee record not found")

    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be positive")

    if req.amount > fee.remaining_amount:
        raise HTTPException(status_code=400, detail=f"Amount exceeds remaining balance of ₹{fee.remaining_amount}")

    # Generate receipt number
    receipt = f"RCP{datetime.now().strftime('%Y%m%d')}{secrets.token_hex(3).upper()}"

    payment = FeePayment(
        fee_id=req.fee_id,
        student_id=fee.student_id,
        amount=req.amount,
        payment_date=datetime.utcnow(),
        payment_method=req.payment_method,
        transaction_id=req.transaction_id,
        receipt_number=receipt,
        installment_number=req.installment_number,
        remarks=req.remarks,
        verified_by=int(payload["sub"]),
    )
    db.add(payment)

    # Update paid_amount on fee
    fee.paid_amount = float(fee.paid_amount) + req.amount
    await db.commit()

    return {"message": "Payment recorded", "receipt_number": receipt}


@router.get("/admin/stats")
async def get_fee_stats(
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    academic_year: str = Query(default="2024-25"),
):
    """Fee collection statistics for admin."""
    result = await db.execute(
        select(
            func.sum(Fee.total_amount).label("total_billed"),
            func.sum(Fee.paid_amount).label("total_collected"),
            func.count(Fee.id).label("total_records"),
        )
        .where(Fee.academic_year == academic_year)
    )
    row = result.one()

    return {
        "academic_year": academic_year,
        "total_billed": float(row.total_billed or 0),
        "total_collected": float(row.total_collected or 0),
        "total_pending": float((row.total_billed or 0) - (row.total_collected or 0)),
        "collection_rate": round(
            (float(row.total_collected or 0) / float(row.total_billed or 1)) * 100, 2
        ),
    }
