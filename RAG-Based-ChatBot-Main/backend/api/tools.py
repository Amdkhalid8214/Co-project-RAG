"""
DocuChat AI - Tool Endpoints & Secure Output File Download
"""
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any

from backend.config import settings
from backend.tools.registry import TOOL_DEFINITIONS, execute_tool

router = APIRouter(prefix="/tools", tags=["tools"])

class ToolExecuteRequest(BaseModel):
    tool: str
    arguments: Dict[str, Any]

@router.get("")
async def list_available_tools():
    """Returns list of registered, safe tools with JSON schemas."""
    return {"tools": TOOL_DEFINITIONS}

@router.post("/execute")
async def execute_tool_endpoint(req: ToolExecuteRequest):
    """Executes a vetted tool safely."""
    result = await execute_tool(req.tool, req.arguments)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/download/{filename}")
async def download_output_file(filename: str):
    """Secure file download preventing path traversal."""
    # Defend against path traversal
    safe_filename = Path(filename).name
    target_path = Path(settings.OUTPUT_DIR) / safe_filename

    # Ensure path stays within settings.OUTPUT_DIR
    resolved_target = target_path.resolve()
    resolved_output_dir = Path(settings.OUTPUT_DIR).resolve()

    if not str(resolved_target).startswith(str(resolved_output_dir)):
        raise HTTPException(status_code=403, detail="Forbidden: Path traversal detected.")

    if not resolved_target.exists():
        raise HTTPException(status_code=404, detail="Requested generated file not found.")

    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if safe_filename.endswith(".xlsx") else "application/octet-stream"

    return FileResponse(
        path=str(resolved_target),
        filename=safe_filename,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={safe_filename}"}
    )
