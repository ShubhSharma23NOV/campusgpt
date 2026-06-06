"""Policy document upload and management endpoints."""

import os
import shutil
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.config import settings
from app.core.security import require_admin, require_any_user
from app.models.policy import Policy
from app.services.ai_service import rag_service

router = APIRouter()

ALLOWED_TYPES = {"application/pdf", "application/x-pdf"}
MAX_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/upload", status_code=201)
async def upload_policy(
    title: str = Form(...),
    category: str = Form(...),
    version: Optional[str] = Form(default=None),
    file: UploadFile = File(...),
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Upload a policy PDF and index it in ChromaDB (admin only)."""
    # Validate file type
    if file.content_type not in ALLOWED_TYPES and not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Read content and check size
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB")

    # Save file
    upload_path = os.path.join(settings.UPLOAD_DIR, "policies")
    os.makedirs(upload_path, exist_ok=True)

    safe_name = f"{category}_{title.replace(' ', '_').lower()}_{os.urandom(4).hex()}.pdf"
    file_path = os.path.join(upload_path, safe_name)

    with open(file_path, "wb") as f:
        f.write(content)

    # Create DB record
    policy = Policy(
        title=title,
        category=category,
        file_name=file.filename,
        file_path=file_path,
        file_size=len(content),
        version=version,
        uploaded_by=int(payload["sub"]),
        is_active=True,
    )
    db.add(policy)
    await db.flush()  # Get the ID

    # Ingest into ChromaDB
    ingest_result = await rag_service.ingest_pdf(
        file_path=file_path,
        policy_id=policy.id,
        title=title,
        category=category,
    )

    if ingest_result["success"]:
        policy.chroma_collection = settings.CHROMA_COLLECTION_NAME
    else:
        # Still save the policy even if indexing fails, can retry
        policy.chroma_collection = None

    await db.commit()

    return {
        "message": "Policy uploaded successfully",
        "policy_id": policy.id,
        "title": title,
        "chunks_indexed": ingest_result.get("chunks", 0),
        "indexed": ingest_result["success"],
    }


@router.get("/")
async def list_policies(
    db: AsyncSession = Depends(get_db),
    category: Optional[str] = None,
):
    """List all active policy documents."""
    query = select(Policy).where(Policy.is_active == True)
    if category:
        query = query.where(Policy.category == category)

    result = await db.execute(query.order_by(Policy.created_at.desc()))
    policies = result.scalars().all()

    return {
        "policies": [
            {
                "id": p.id,
                "title": p.title,
                "category": p.category,
                "version": p.version,
                "file_name": p.file_name,
                "file_size": p.file_size,
                "summary": p.summary,
                "is_indexed": p.chroma_collection is not None,
                "effective_date": str(p.effective_date) if p.effective_date else None,
                "created_at": str(p.created_at),
            }
            for p in policies
        ]
    }


@router.get("/{policy_id}")
async def get_policy(policy_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific policy."""
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    return {
        "id": policy.id,
        "title": policy.title,
        "category": policy.category,
        "version": policy.version,
        "file_name": policy.file_name,
        "file_path": policy.file_path,
        "file_size": policy.file_size,
        "summary": policy.summary,
        "language": policy.language,
        "effective_date": str(policy.effective_date) if policy.effective_date else None,
        "is_indexed": policy.chroma_collection is not None,
        "created_at": str(policy.created_at),
    }


@router.delete("/{policy_id}")
async def delete_policy(
    policy_id: int,
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a policy (admin only)."""
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    policy.is_active = False
    await db.commit()
    return {"message": "Policy deactivated"}


@router.post("/{policy_id}/reindex")
async def reindex_policy(
    policy_id: int,
    payload: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Re-index an existing policy document in ChromaDB."""
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    if not os.path.exists(policy.file_path):
        raise HTTPException(status_code=404, detail="Policy file not found on disk")

    ingest_result = await rag_service.ingest_pdf(
        file_path=policy.file_path,
        policy_id=policy.id,
        title=policy.title,
        category=policy.category,
    )

    if ingest_result["success"]:
        policy.chroma_collection = settings.CHROMA_COLLECTION_NAME
        await db.commit()

    return {
        "success": ingest_result["success"],
        "chunks_indexed": ingest_result.get("chunks", 0),
        "error": ingest_result.get("error"),
    }
