"""AI Chat endpoints – Policy Navigator and Personalized Assistant."""

import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import require_student, require_any_user, optional_oauth2, decode_token
from app.models.student import Student
from app.models.attendance import AttendanceSummary, Subject
from app.models.fees import Fee
from app.models.hostel import HostelAllocation, Hostel
from app.models.scholarship import ScholarshipApplication, Scholarship
from app.models.fine import Fine
from app.services.ai_service import rag_service

router = APIRouter()

# In-memory session store (use Redis in production)
_sessions: dict[str, list[dict]] = {}


# ─── Schemas ─────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    mode: str = "policy"  # "policy" | "personalized"
    language: str = "english"


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]
    session_id: str
    was_answered: bool
    response_time: float


# ─── Helper: Get Student Data ─────────────────────────────

async def _get_student_context(student_id: int, db: AsyncSession) -> dict:
    """Fetch all student data for personalized AI responses."""
    # Student basic info
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        return {}

    # Attendance
    att_result = await db.execute(
        select(AttendanceSummary, Subject)
        .join(Subject, AttendanceSummary.subject_id == Subject.id)
        .where(AttendanceSummary.student_id == student_id)
    )
    attendance_data = []
    for summary, subject in att_result.all():
        attendance_data.append({
            "subject_name": subject.name,
            "subject_code": subject.code,
            "attended": summary.attended_classes,
            "total": summary.total_classes,
            "percentage": summary.percentage,
        })

    # Fees
    fee_result = await db.execute(select(Fee).where(Fee.student_id == student_id))
    fees_data = []
    for fee in fee_result.scalars().all():
        fees_data.append({
            "fee_type": fee.fee_type,
            "total_amount": float(fee.total_amount),
            "paid_amount": float(fee.paid_amount),
            "remaining": fee.remaining_amount,
            "due_date": str(fee.due_date) if fee.due_date else None,
            "status": fee.status,
        })

    # Hostel
    hostel_result = await db.execute(
        select(HostelAllocation, Hostel)
        .join(Hostel, HostelAllocation.hostel_id == Hostel.id)
        .where(HostelAllocation.student_id == student_id, HostelAllocation.status == "active")
    )
    hostel_row = hostel_result.first()
    hostel_data = None
    if hostel_row:
        alloc, room = hostel_row
        hostel_data = {
            "hostel_name": room.hostel_name,
            "room_number": room.room_number,
            "room_type": room.room_type,
            "remaining_fee": alloc.remaining_fee,
            "next_due_date": str(alloc.next_due_date) if alloc.next_due_date else None,
        }

    # Scholarships
    sch_result = await db.execute(
        select(ScholarshipApplication, Scholarship)
        .join(Scholarship, ScholarshipApplication.scholarship_id == Scholarship.id)
        .where(ScholarshipApplication.student_id == student_id)
    )
    scholarships_data = []
    for app, sch in sch_result.all():
        scholarships_data.append({
            "name": sch.name,
            "type": sch.type,
            "amount": float(sch.amount),
            "status": app.status,
            "approved_amount": float(app.approved_amount) if app.approved_amount else None,
        })

    # Fines
    fine_result = await db.execute(select(Fine).where(Fine.student_id == student_id))
    fines_data = []
    for fine in fine_result.scalars().all():
        fines_data.append({
            "reason": fine.reason,
            "amount": float(fine.amount),
            "paid_amount": float(fine.paid_amount),
            "remaining_amount": fine.remaining_amount,
            "status": fine.status,
            "due_date": str(fine.due_date) if fine.due_date else None,
        })

    return {
        "student": {
            "name": student.name,
            "student_id": student.student_id,
            "course": student.course,
            "semester": student.semester,
            "category": student.category,
            "is_hostel_student": student.is_hostel_student,
        },
        "attendance": attendance_data,
        "fees": fees_data,
        "hostel": hostel_data,
        "scholarships": scholarships_data,
        "fines": fines_data,
    }


# ─── Endpoints ───────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Depends(optional_oauth2),
):
    """Main AI chat endpoint. Supports both policy and personalized modes."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Session management
    session_id = req.session_id or str(uuid.uuid4())
    if session_id not in _sessions:
        _sessions[session_id] = []

    history = _sessions[session_id]

    # Get user info if authenticated
    student_id = None
    if token:
        try:
            payload = decode_token(token)
            if payload.get("user_type") == "student":
                student_id = int(payload["sub"])
        except Exception:
            pass

    # Route to correct mode
    if req.mode == "personalized" and student_id:
        student_data = await _get_student_context(student_id, db)
        result = await rag_service.chat_personalized(
            question=req.question,
            student_data=student_data,
            session_history=history,
        )
    else:
        result = await rag_service.chat_policy(
            question=req.question,
            session_history=history,
        )

    # Update session history
    _sessions[session_id].append({"role": "user", "content": req.question})
    _sessions[session_id].append({"role": "assistant", "content": result["answer"]})

    # Keep last 20 messages
    if len(_sessions[session_id]) > 20:
        _sessions[session_id] = _sessions[session_id][-20:]

    # Log to DB
    try:
        from app.models.policy import Policy  # noqa
        # Could insert into chat_history table here
        pass
    except Exception:
        pass

    return ChatResponse(
        answer=result["answer"],
        sources=result.get("sources", []),
        session_id=session_id,
        was_answered=result.get("was_answered", True),
        response_time=result.get("response_time", 0),
    )


@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session."""
    history = _sessions.get(session_id, [])
    return {"session_id": session_id, "messages": history}


@router.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear chat session."""
    _sessions.pop(session_id, None)
    return {"message": "Chat history cleared"}


@router.get("/attendance-advice")
async def get_attendance_advice(
    payload: dict = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Get AI-powered attendance advice for the logged-in student."""
    student_id = int(payload["sub"])

    att_result = await db.execute(
        select(AttendanceSummary, Subject)
        .join(Subject, AttendanceSummary.subject_id == Subject.id)
        .where(AttendanceSummary.student_id == student_id)
    )
    attendance_data = []
    for summary, subject in att_result.all():
        attendance_data.append({
            "subject_name": subject.name,
            "attended": summary.attended_classes,
            "total": summary.total_classes,
            "percentage": summary.percentage,
        })

    if not attendance_data:
        return {"advice": "No attendance data available yet."}

    advice = await rag_service.get_attendance_advice(attendance_data)
    return {"advice": advice, "subjects": attendance_data}


@router.post("/summarize-policy/{policy_id}")
async def summarize_policy(
    policy_id: int,
    payload: dict = Depends(require_any_user),
    db: AsyncSession = Depends(get_db),
):
    """Summarize a policy document."""
    from app.models.policy import Policy
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()

    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    summary = await rag_service.summarize_policy(policy_id, policy.title)
    return {"policy_id": policy_id, "title": policy.title, "summary": summary}
