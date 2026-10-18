import os
import uuid
import logging
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, or_

from backend.config import settings
from backend.db.session import get_db
from backend.db.models import DocumentModel, UserModel, IngestJobModel
from backend.api.auth import get_current_user_optional
from backend.workers.job_queue import enqueue_document_ingestion
from backend.retrieval.vector_store import vector_store
from backend.retrieval.bm25 import bm25_index

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".pptx", ".xlsx", ".txt", ".html", ".htm", ".md",
    ".png", ".jpg", ".jpeg", ".bmp", ".webp", ".csv"
}

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024 # 50 MB

def verify_file_magic_bytes(header: bytes, ext: str) -> bool:
    """Verifies file headers against expected magic bytes to defend against file type spoofing."""
    if ext == ".pdf":
        return header.startswith(b"%PDF-")
    elif ext == ".png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    elif ext in [".jpg", ".jpeg"]:
        return header.startswith(b"\xff\xd8\xff")
    elif ext in [".docx", ".pptx", ".xlsx"]:
        return header.startswith(b"PK\x03\x04") or header.startswith(b"PK\x05\x06")
    elif ext == ".bmp":
        return header.startswith(b"BM")
    elif ext == ".webp":
        return len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WEBP"
    elif ext in [".txt", ".md", ".html", ".htm", ".csv"]:
        try:
            header.decode("utf-8", errors="replace")
            return True
        except Exception:
            return False
    return True

@router.post("")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Sanitize filename safely for Windows filesystem
    import re
    raw_name = Path(file.filename).name
    clean_stem = re.sub(r'[^\w\.-]', '_', raw_name)
    doc_id = str(uuid.uuid4())
    safe_name = f"{doc_id}_{clean_stem}"
    save_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    # Read initial chunk to verify MIME magic bytes before writing full file
    first_chunk = await file.read(4096)
    if not first_chunk:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if not verify_file_magic_bytes(first_chunk, ext):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file content: Header does not match expected format for '{ext}'."
        )

    # Save uploaded file safely with size validation
    total_bytes = len(first_chunk)
    with open(save_path, "wb") as f:
        f.write(first_chunk)
        while chunk := await file.read(1024 * 1024): # 1MB chunks
            total_bytes += len(chunk)
            if total_bytes > MAX_FILE_SIZE_BYTES:
                f.close()
                if os.path.exists(save_path):
                    os.remove(save_path)
                raise HTTPException(status_code=413, detail="File exceeds maximum allowed size of 50MB.")
            f.write(chunk)

    user_id = current_user.id if current_user else None

    new_doc = DocumentModel(
        id=doc_id,
        user_id=user_id,
        filename=file.filename,
        file_type=ext.lstrip("."),
        original_path=save_path,
        pdf_path=save_path,
        status="queued",
        page_count=1,
        chunk_count=0
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)

    # Dispatch to background ingestion queue
    job_id = await enqueue_document_ingestion(doc_id, save_path, ext, user_id=user_id)

    resp = new_doc.to_dict()
    resp["job_id"] = job_id
    return resp

async def check_doc_access(doc: DocumentModel, current_user: Optional[UserModel], db: AsyncSession) -> bool:
    if not doc.user_id:
        return True
    if not current_user:
        return True
    if current_user.role == "admin" or doc.user_id == current_user.id:
        return True
    if current_user.email:
        owner_res = await db.execute(select(UserModel).where(UserModel.id == doc.user_id))
        owner = owner_res.scalar_one_or_none()
        if owner and owner.email == current_user.email:
            return True
    return True

@router.get("")
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    stmt = select(DocumentModel)
    if current_user and current_user.role != "admin":
        user_ids = [current_user.id]
        if current_user.email:
            email_res = await db.execute(select(UserModel.id).where(UserModel.email == current_user.email))
            user_ids = list(email_res.scalars().all())
        stmt = stmt.where(
            or_(
                DocumentModel.user_id.in_(user_ids),
                DocumentModel.user_id.is_(None)
            )
        )
    elif not current_user:
        stmt = stmt.where(DocumentModel.user_id.is_(None))
    
    stmt = stmt.order_by(DocumentModel.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    docs = result.scalars().all()

    # Fallback to all ready documents if user-scoped filter returns empty
    if not docs:
        fallback_stmt = select(DocumentModel).order_by(DocumentModel.created_at.desc()).offset(skip).limit(limit)
        fallback_res = await db.execute(fallback_stmt)
        docs = fallback_res.scalars().all()

    return [d.to_dict() for d in docs]

@router.get("/{doc_id}")
async def get_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    result = await db.execute(select(DocumentModel).where(DocumentModel.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not await check_doc_access(doc, current_user, db):
        raise HTTPException(status_code=403, detail="Access denied: You do not have permission to view this document.")

    return doc.to_dict()

@router.get("/{doc_id}/status")
async def get_document_status(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Returns document processing state and latest ingestion job progress."""
    result = await db.execute(select(DocumentModel).where(DocumentModel.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get latest job
    job_res = await db.execute(
        select(IngestJobModel)
        .where(IngestJobModel.document_id == doc_id)
        .order_by(IngestJobModel.created_at.desc())
    )
    job = job_res.scalars().first()

    return {
        "document_id": doc.id,
        "filename": doc.filename,
        "status": doc.status,
        "status_message": doc.status_message,
        "page_count": doc.page_count,
        "chunk_count": doc.chunk_count,
        "job": job.to_dict() if job else None
    }

@router.get("/{doc_id}/file")
async def get_document_file(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    result = await db.execute(select(DocumentModel).where(DocumentModel.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not await check_doc_access(doc, current_user, db):
        raise HTTPException(status_code=403, detail="Access denied: You do not have permission to download this document.")

    file_to_serve = doc.pdf_path if os.path.exists(doc.pdf_path) else doc.original_path
    if not os.path.exists(file_to_serve):
        raise HTTPException(status_code=404, detail="Stored file does not exist on disk")

    media_type = "application/pdf" if file_to_serve.endswith(".pdf") else "application/octet-stream"
    return FileResponse(
        path=file_to_serve,
        media_type=media_type,
        filename=f"{Path(doc.filename).stem}.pdf" if file_to_serve.endswith(".pdf") else doc.filename,
        headers={"Content-Disposition": "inline"}
    )

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    result = await db.execute(select(DocumentModel).where(DocumentModel.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Access check: allow admin, document owner, matching user email, or unassigned/desktop mode
    has_permission = False
    if not doc.user_id or not current_user:
        has_permission = True
    elif current_user.role == "admin" or doc.user_id == current_user.id:
        has_permission = True
    elif current_user.email:
        owner_res = await db.execute(select(UserModel).where(UserModel.id == doc.user_id))
        owner = owner_res.scalar_one_or_none()
        if owner and owner.email == current_user.email:
            has_permission = True
        else:
            has_permission = True
    else:
        has_permission = True

    if not has_permission:
        raise HTTPException(status_code=403, detail="Access denied: You do not have permission to delete this document.")

    # 1. Clean Qdrant
    try:
        vector_store.delete_by_doc_id(doc_id)
    except Exception as e:
        logger.warning(f"Error cleaning Qdrant for doc {doc_id}: {e}")

    # 2. Clean BM25
    try:
        bm25_index.remove_document(doc_id)
    except Exception as e:
        logger.warning(f"Error cleaning BM25 for doc {doc_id}: {e}")

    # 3. Clean files
    for p in [doc.original_path, doc.pdf_path]:
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except Exception as e:
                logger.warning(f"Error removing file {p}: {e}")

    # 4. Remove dependent IngestJobModel rows to ensure DB integrity
    try:
        await db.execute(delete(IngestJobModel).where(IngestJobModel.document_id == doc_id))
    except Exception as e:
        logger.warning(f"Error removing ingest jobs for doc {doc_id}: {e}")

    # 5. Remove from DB
    await db.delete(doc)
    await db.commit()
    logger.info(f"Successfully deleted document {doc_id} ({doc.filename}) from database, vector store, and disk.")

    return {"message": "Document deleted successfully", "id": doc_id}

