"""
DocuChat AI - Safe Excel Export Tool
Generates tabular spreadsheets with openpyxl in a controlled directory.
Strictly sanitizes cell inputs to protect against CSV/Excel formula injection.
"""
import os
import re
import uuid
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from backend.config import settings

logger = logging.getLogger("excel_generator")

def sanitize_cell_value(val: Any) -> Any:
    """
    Prevents spreadsheet formula injection (CWE-1236).
    If a cell value starts with '=', '+', '-', '@', tab, or carriage return,
    prepend an apostrophe to force Excel to treat it as a literal string.
    """
    if isinstance(val, str) and val:
        if val[0] in ('=', '+', '-', '@', '\t', '\r') or (val.strip() and val.strip()[0] in ('=', '+', '-', '@')):
            return f"'{val}"
    return val


def generate_excel_sheet(
    title: str,
    headers: List[str],
    rows: List[List[Any]],
    filename_prefix: Optional[str] = "report"
) -> Dict[str, Any]:
    """
    Safely creates an Excel workbook in settings.OUTPUT_DIR with formula injection defense.
    """
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    
    # Sanitize prefix and create safe collision-resistant filename
    clean_prefix = re.sub(r"[^a-zA-Z0-9_\-]", "_", filename_prefix or "report")[:30]
    file_id = str(uuid.uuid4())[:8]
    filename = f"{clean_prefix}_{file_id}.xlsx"
    file_path = os.path.join(settings.OUTPUT_DIR, filename)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = re.sub(r"[\\/*?:\[\]]", "_", title)[:31] or "Data"

    # Header styling
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Write headers
    clean_headers = [sanitize_cell_value(h) for h in headers]
    ws.append(clean_headers)
    for col_idx in range(1, len(clean_headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    # Write data rows
    for row in rows:
        clean_row = [sanitize_cell_value(c) for c in row]
        ws.append(clean_row)

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 50)

    wb.save(file_path)
    wb.close()

    logger.info(f"Generated safe Excel report at {file_path} with {len(rows)} rows.")
    return {
        "filename": filename,
        "path": file_path,
        "row_count": len(rows),
        "column_count": len(headers),
        "download_url": f"/api/tools/download/{filename}"
    }
