"""
Unit and integration test for background worker zombie recovery.
Ensures jobs and documents stuck in active processing states from server crashes
are safely recovered and marked as failed with diagnostic guidance.
"""
import pytest
import uuid
from sqlalchemy import select
from backend.db.session import AsyncSessionLocal, init_db
from backend.db.models import DocumentModel, IngestJobModel
from backend.workers.ingest_worker import recover_zombie_jobs


@pytest.mark.asyncio
async def test_recover_zombie_jobs_lifecycle():
    await init_db()

    test_doc_id = f"test_zombie_doc_{uuid.uuid4().hex[:8]}"
    test_job_id = f"test_zombie_job_{uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as session:
        # Create an orphaned document stuck in "processing"
        doc = DocumentModel(
            id=test_doc_id,
            filename="crash_simulation.pdf",
            file_type="pdf",
            original_path="C:/fake/crash_simulation.pdf",
            pdf_path="C:/fake/crash_simulation.pdf",
            status="processing",
            user_id="default_user"
        )
        session.add(doc)

        # Create an orphaned job stuck in "chunking"
        job = IngestJobModel(
            id=test_job_id,
            document_id=test_doc_id,
            status="chunking",
            progress=65,
            message="Processing elements before power failure"
        )
        session.add(job)
        await session.commit()

    # Run zombie recovery
    result = await recover_zombie_jobs()
    assert result["recovered_jobs"] >= 1
    assert result["recovered_docs"] >= 1

    # Verify persistent state in DB
    async with AsyncSessionLocal() as session:
        updated_doc = (await session.execute(
            select(DocumentModel).where(DocumentModel.id == test_doc_id)
        )).scalar_one()

        updated_job = (await session.execute(
            select(IngestJobModel).where(IngestJobModel.id == test_job_id)
        )).scalar_one()

        assert updated_doc.status == "failed"
        assert "interrupted" in updated_doc.status_message.lower()

        assert updated_job.status == "failed"
        assert "interrupted" in updated_job.message.lower()

        # Clean up test rows
        await session.delete(updated_job)
        await session.delete(updated_doc)
        await session.commit()
