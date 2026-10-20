"""
DocuChat AI - Safe Excel & Spreadsheet Analysis Tool
Performs verified metadata inspection, calculations (sum, average, min, max, count),
department/category grouping, and column filtering using openpyxl and pandas.
Prevents arbitrary code execution and formula injection.
Integrates with LangChain tool-calling loop and ContextVar conversation document scoping.
"""

import os
import re
import json
import logging
from contextvars import ContextVar
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

import openpyxl
from openpyxl.utils import get_column_letter
import pandas as pd
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from backend.config import settings

logger = logging.getLogger("excel_analyzer")

# ContextVar for propagating active document information into tool calls within async task context
active_excel_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar("active_excel_context", default=None)


class ExcelAnalysisInput(BaseModel):
    operation: str = Field(
        ...,
        description="Analysis operation: 'metadata' (sheets, row/col count, column names), 'sum'/'total', 'average'/'mean', 'max'/'highest', 'min'/'lowest', 'count', 'groupby', 'filter', or 'summary'."
    )
    column: Optional[str] = Field(
        None,
        description="Target column name to calculate or inspect (e.g. 'Sales', 'Target', 'Employee'). Case-insensitive."
    )
    group_by: Optional[str] = Field(
        None,
        description="Column name to group rows by (e.g. 'Department')."
    )
    filter_column: Optional[str] = Field(
        None,
        description="Column name to filter rows on (e.g. 'Department')."
    )
    filter_value: Optional[str] = Field(
        None,
        description="Value to match for the filter (e.g. 'IT', 'Sales', 'HR')."
    )
    sheet_name: Optional[str] = Field(
        None,
        description="Worksheet name if workbook contains multiple sheets (defaults to active sheet)."
    )
    doc_id: Optional[str] = Field(
        None,
        description="Document ID of the spreadsheet. If omitted, automatically resolved from conversation context."
    )


def resolve_spreadsheet_file(doc_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Resolves the spreadsheet file path and metadata using:
    1. Explicit doc_id argument.
    2. Active conversation ContextVar.
    3. Document store in UPLOAD_DIR.
    """
    ctx = active_excel_context.get() or {}
    resolved_id = doc_id or ctx.get("doc_id")

    # If no doc_id was passed and context has a file_path that exists, use it
    if not resolved_id and ctx.get("file_path") and os.path.exists(ctx["file_path"]):
        return {
            "doc_id": ctx.get("doc_id", "active_context"),
            "file_path": ctx["file_path"],
            "filename": ctx.get("filename", Path(ctx["file_path"]).name)
        }

    # Search for file by doc_id in UPLOAD_DIR
    upload_dir = Path(settings.UPLOAD_DIR)
    if resolved_id:
        # Match pattern {resolved_id}_*
        candidates = list(upload_dir.glob(f"{resolved_id}_*"))
        if candidates:
            cand = candidates[0]
            ext = cand.suffix.lower()
            if ext in (".xlsx", ".xls", ".csv"):
                return {
                    "doc_id": resolved_id,
                    "file_path": str(cand),
                    "filename": cand.name.split("_", 1)[-1] if "_" in cand.name else cand.name
                }
            else:
                raise ValueError(f"Document {resolved_id} format '{ext}' is not a supported spreadsheet format.")
        elif doc_id:
            # Explicit doc_id requested but not found
            raise FileNotFoundError(f"Spreadsheet document with ID '{doc_id}' was not found.")

    # Fallback: check context doc_ids list
    doc_ids_list = ctx.get("doc_ids") or []
    for d_id in doc_ids_list:
        candidates = list(upload_dir.glob(f"{d_id}_*"))
        for cand in candidates:
            if cand.suffix.lower() in (".xlsx", ".xls", ".csv"):
                return {
                    "doc_id": d_id,
                    "file_path": str(cand),
                    "filename": cand.name.split("_", 1)[-1] if "_" in cand.name else cand.name
                }

    # Fallback: discover any ready spreadsheet in UPLOAD_DIR
    for ext in ("*.xlsx", "*.xls", "*.csv"):
        for cand in upload_dir.glob(ext):
            return {
                "doc_id": cand.name.split("_", 1)[0] if "_" in cand.name else "local",
                "file_path": str(cand),
                "filename": cand.name.split("_", 1)[-1] if "_" in cand.name else cand.name
            }

    raise FileNotFoundError("No active spreadsheet document was found in the current conversation context.")


def _find_column(df: pd.DataFrame, target: Optional[str]) -> Optional[str]:
    """Case-insensitive and whitespace-tolerant column matching."""
    if not target or not isinstance(target, str):
        return None
    target_clean = target.strip().lower()
    for col in df.columns:
        if str(col).strip().lower() == target_clean:
            return col
    # Partial match fallback (e.g. 'sale' matching 'Sales')
    for col in df.columns:
        if target_clean in str(col).strip().lower() or str(col).strip().lower() in target_clean:
            return col
    return None


def execute_excel_analysis(
    operation: str,
    column: Optional[str] = None,
    group_by: Optional[str] = None,
    filter_column: Optional[str] = None,
    filter_value: Optional[str] = None,
    sheet_name: Optional[str] = None,
    doc_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes spreadsheet analysis using openpyxl and pandas.
    Returns structured dictionary with metadata and calculated metrics.
    """
    # 1. Resolve spreadsheet file
    try:
        resolved = resolve_spreadsheet_file(doc_id)
    except Exception as e:
        logger.error(f"[EXCEL_ANALYZER] File resolution failed: {e}")
        return {"status": "error", "message": str(e)}

    file_path = resolved["file_path"]
    filename = resolved["filename"]
    ext = Path(file_path).suffix.lower()

    logger.info(f"[EXCEL_ANALYZER] Selected tool for document '{filename}' (ID: {resolved['doc_id']}), op='{operation}', col='{column}'")

    try:
        # Load workbook sheets
        if ext in (".xlsx", ".xls"):
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            sheet_names = wb.sheetnames
            active_sheet = sheet_name if sheet_name and sheet_name in sheet_names else sheet_names[0]
            ws = wb[active_sheet]
            raw_rows = list(ws.iter_rows(values_only=True))
            wb.close()

            if not raw_rows:
                return {
                    "status": "success",
                    "filename": filename,
                    "sheet_names": sheet_names,
                    "active_sheet": active_sheet,
                    "data_rows": 0,
                    "total_columns": 0,
                    "columns": [],
                    "message": f"Worksheet '{active_sheet}' is empty."
                }

            header = [str(c).strip() if c is not None and str(c).strip() != "" else f"Column_{i+1}" for i, c in enumerate(raw_rows[0])]
            data_rows = raw_rows[1:]
            total_cols = len(header)
            dims = f"A1:{get_column_letter(total_cols)}{len(data_rows) + 1}"

            # Convert to DataFrame for calculations
            df = pd.DataFrame(data_rows, columns=header)
        else:
            # CSV file
            df = pd.read_csv(file_path)
            sheet_names = ["CSV Data"]
            active_sheet = "CSV Data"
            dims = f"A1:{get_column_letter(len(df.columns))}{len(df) + 1}"

        total_rows = len(df)
        total_columns = len(df.columns)
        columns_list = list(df.columns)

        # Clean numeric columns (convert currency/commas to numbers)
        for col in df.columns:
            if df[col].dtype == object:
                # Try stripping commas and whitespace
                converted = pd.to_numeric(df[col].astype(str).str.replace(",", "").str.strip(), errors="coerce")
                # If majority are valid numbers, replace column
                if converted.notnull().sum() >= max(1, int(len(df) * 0.6)):
                    df[col] = converted

        op_lower = (operation or "metadata").strip().lower()

        # Operation 1: Metadata & Structure inspection
        if op_lower in ("metadata", "info", "structure", "columns", "sheets"):
            return {
                "status": "success",
                "filename": filename,
                "sheet_names": sheet_names,
                "active_sheet": active_sheet,
                "total_sheets": len(sheet_names),
                "data_rows": total_rows,
                "total_columns": total_columns,
                "columns": columns_list,
                "dimensions": dims,
                "summary": (
                    f"Workbook '{filename}' contains {len(sheet_names)} sheet(s): {', '.join(sheet_names)}. "
                    f"Active sheet '{active_sheet}' has {total_rows} data rows and {total_columns} columns: "
                    f"{', '.join(columns_list)}."
                )
            }

        # Apply row filter if specified
        target_df = df
        filter_matched_col = _find_column(df, filter_column)
        if filter_matched_col and filter_value is not None:
            val_clean = str(filter_value).strip().lower()
            target_df = df[df[filter_matched_col].astype(str).str.strip().str.lower() == val_clean]

        target_col = _find_column(target_df, column)

        # Operation 2: Group By calculation (e.g. group by Department, sum Sales)
        grp_col = _find_column(df, group_by)
        if op_lower in ("groupby", "group_by") or grp_col is not None:
            if not grp_col:
                # Look for typical grouping column (e.g. Department, Category)
                grp_col = _find_column(df, "Department") or _find_column(df, "Category")
            if not target_col:
                # Default to numeric column
                num_cols = target_df.select_dtypes(include=["number"]).columns
                target_col = num_cols[0] if len(num_cols) > 0 else None

            if grp_col and target_col:
                grouped = target_df.groupby(grp_col)[target_col].agg(["sum", "mean", "count"]).reset_index()
                dept_dict = {}
                for _, row in grouped.iterrows():
                    dept_dict[str(row[grp_col])] = {
                        "total": float(row["sum"]),
                        "average": float(round(row["mean"], 2)),
                        "count": int(row["count"])
                    }
                return {
                    "status": "success",
                    "filename": filename,
                    "operation": "groupby",
                    "group_by_column": grp_col,
                    "target_column": target_col,
                    "grouped_results": dept_dict,
                    "summary": f"Grouped {target_col} by {grp_col}: " + "; ".join(f"{k}: total {v['total']}" for k, v in dept_dict.items())
                }

        # If target column is required for math but not found, try finding first numeric column
        if not target_col and op_lower in ("sum", "total", "average", "mean", "avg", "max", "highest", "min", "lowest"):
            num_cols = target_df.select_dtypes(include=["number"]).columns
            target_col = num_cols[0] if len(num_cols) > 0 else None

        if not target_col and op_lower != "summary":
            return {
                "status": "error",
                "message": f"Column '{column}' was not found in spreadsheet. Available columns: {columns_list}"
            }

        # Operation 3: Total / Sum
        if op_lower in ("sum", "total"):
            total_val = float(target_df[target_col].sum())
            return {
                "status": "success",
                "filename": filename,
                "operation": "sum",
                "column": target_col,
                "filter": {filter_matched_col: filter_value} if filter_matched_col else None,
                "result": total_val,
                "formatted": f"{total_val:,.2f}".rstrip("0").rstrip("."),
                "rows_calculated": len(target_df)
            }

        # Operation 4: Average / Mean
        if op_lower in ("average", "mean", "avg"):
            avg_val = float(target_df[target_col].mean()) if len(target_df) > 0 else 0.0
            return {
                "status": "success",
                "filename": filename,
                "operation": "average",
                "column": target_col,
                "filter": {filter_matched_col: filter_value} if filter_matched_col else None,
                "result": avg_val,
                "formatted": f"{avg_val:,.2f}".rstrip("0").rstrip("."),
                "rows_calculated": len(target_df)
            }

        # Operation 5: Max / Highest
        if op_lower in ("max", "highest"):
            max_idx = target_df[target_col].idxmax()
            max_val = float(target_df[target_col].max())
            best_row = target_df.loc[max_idx].to_dict() if pd.notnull(max_idx) else {}
            return {
                "status": "success",
                "filename": filename,
                "operation": "max",
                "column": target_col,
                "result": max_val,
                "formatted": f"{max_val:,.2f}".rstrip("0").rstrip("."),
                "row_details": {str(k): v for k, v in best_row.items()}
            }

        # Operation 6: Min / Lowest
        if op_lower in ("min", "lowest"):
            min_idx = target_df[target_col].idxmin()
            min_val = float(target_df[target_col].min())
            worst_row = target_df.loc[min_idx].to_dict() if pd.notnull(min_idx) else {}
            return {
                "status": "success",
                "filename": filename,
                "operation": "min",
                "column": target_col,
                "result": min_val,
                "formatted": f"{min_val:,.2f}".rstrip("0").rstrip("."),
                "row_details": {str(k): v for k, v in worst_row.items()}
            }

        # Operation 7: Comprehensive Summary
        numeric_cols = df.select_dtypes(include=["number"]).columns
        num_summary = {}
        for nc in numeric_cols:
            num_summary[nc] = {
                "total": float(df[nc].sum()),
                "average": float(round(df[nc].mean(), 2)),
                "max": float(df[nc].max()),
                "min": float(df[nc].min()),
            }

        return {
            "status": "success",
            "filename": filename,
            "sheet_names": sheet_names,
            "active_sheet": active_sheet,
            "data_rows": total_rows,
            "total_columns": total_columns,
            "columns": columns_list,
            "numeric_metrics": num_summary
        }

    except Exception as e:
        logger.error(f"[EXCEL_ANALYZER] Error executing '{operation}' on '{filename}': {e}", exc_info=True)
        return {"status": "error", "message": f"Spreadsheet analysis failed: {str(e)}"}


@tool("excel_analyzer", args_schema=ExcelAnalysisInput)
def excel_analyzer_tool(
    operation: str,
    column: Optional[str] = None,
    group_by: Optional[str] = None,
    filter_column: Optional[str] = None,
    filter_value: Optional[str] = None,
    sheet_name: Optional[str] = None,
    doc_id: Optional[str] = None
) -> str:
    """
    Analyzes uploaded Excel workbooks (.xlsx, .xls) and CSV spreadsheets.
    Use this tool whenever questions ask for:
    - Sheet names, row counts, column counts, column names
    - Totals, sums, averages, maximums, minimums on columns (e.g. Sales, Target)
    - Grouping data by department or category
    - Filtering specific departments or records
    """
    res = execute_excel_analysis(
        operation=operation,
        column=column,
        group_by=group_by,
        filter_column=filter_column,
        filter_value=filter_value,
        sheet_name=sheet_name,
        doc_id=doc_id
    )
    return json.dumps(res, default=str)
