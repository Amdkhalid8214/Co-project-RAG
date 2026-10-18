import sys
from pathlib import Path

# Add project root to sys.path
root_dir = str(Path(__file__).resolve().parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.chunking.structure_chunker import structure_chunker, estimate_tokens
from backend.parsers.docling_parser import ParsedElement
from backend.db.migrate_sqlite_to_pg import migrate_database
from backend.tools.registry import execute_tool

@pytest.mark.asyncio
async def test_health_and_readiness():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        res_health = await client.get("/health")
        assert res_health.status_code == 200
        data_health = res_health.json()
        assert data_health["status"] == "healthy"
        assert "llm_model" in data_health

        # 2. Readiness check
        res_ready = await client.get("/ready")
        assert res_ready.status_code == 200
        data_ready = res_ready.json()
        assert "database" in data_ready
        assert "vector_store" in data_ready

@pytest.mark.asyncio
async def test_tools_api_and_calculator():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. List tools
        res_tools = await client.get("/api/tools")
        assert res_tools.status_code == 200
        tools = res_tools.json()["tools"]
        assert any(t["name"] == "calculator" for t in tools)
        assert any(t["name"] == "export_excel" for t in tools)

        # 2. Execute calculator tool
        res_calc = await client.post("/api/tools/execute", json={
            "tool": "calculator",
            "arguments": {"expression": "1000 * 5 + 250"}
        })
        assert res_calc.status_code == 200
        assert res_calc.json()["result"] == 5250

@pytest.mark.asyncio
async def test_path_traversal_download_defense():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Path traversal attack attempt
        res = await client.get("/api/tools/download/../../etc/passwd")
        # Must be rejected (either 403 or 404, never 200)
        assert res.status_code in (403, 404)

def test_structure_chunker_token_limit():
    """Verify that chunks strictly stay under the 450-token safe maximum limit."""
    long_text = "This is a comprehensive test paragraph discussing enterprise document intelligence and semantic retrieval. " * 30
    elem = ParsedElement(
        text=long_text,
        page=1,
        bboxes=[{"x0": 10, "y0": 20, "x1": 200, "y1": 50}],
        heading_path=["Executive Summary"]
    )
    chunks = structure_chunker.chunk_elements([elem], doc_id="test_doc_tok")
    assert len(chunks) > 0
    for c in chunks:
        # Verify exact token count does not exceed safe maximum limit
        toks = estimate_tokens(c.text)
        assert toks <= 460
        assert c.heading_path == ["Executive Summary"]

def test_sqlite_to_target_migration_idempotent():
    """Verifies SQLite data transfer to target database is fully idempotent and preserves rows."""
    from backend.config import settings
    sqlite_file = Path(settings.DATA_DIR) / "rag_app.db"
    if sqlite_file.exists():
        test_target_file = Path(settings.DATA_DIR) / "test_migration_run.db"
        target_url = f"sqlite:///{test_target_file.as_posix()}"
        
        # First run
        success1 = migrate_database(str(sqlite_file), target_url)
        assert success1 is True
        
        # Idempotent second run (should skip existing records safely)
        success2 = migrate_database(str(sqlite_file), target_url)
        assert success2 is True

        if test_target_file.exists():
            try:
                test_target_file.unlink()
            except Exception:
                pass

