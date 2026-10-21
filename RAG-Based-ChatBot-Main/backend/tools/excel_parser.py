"""
DocuChat AI - Structured Excel Generation Request Parser
Extracts validated dimensions, dataset types, and operation parameters from the CURRENT user request.
Ensures no dimension or schema leaks from prior conversational turns.
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger("excel_parser")

# Configured boundary limits
MIN_DATA_ROWS = 1
MAX_DATA_ROWS = 5000
MIN_DATA_COLS = 1
MAX_DATA_COLS = 100


class ParsedExcelRequest(BaseModel):
    operation: str = "generate_workbook"
    dataset_type: str = "general_tabular"
    data_rows: int = 25
    data_columns: int = 7
    worksheet_count: int = 1
    include_summary: bool = False
    source: str = "synthetic_data"
    output_format: str = "xlsx"
    is_qa: bool = False
    application_name: str = "Custom Spreadsheet"
    title: str = "Spreadsheet"
    prefix: str = "spreadsheet"
    raw_prompt: str = ""


def parse_number_match(text: str, patterns: list) -> Optional[int]:
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            try:
                return int(m.group(1))
            except (ValueError, TypeError):
                continue
    return None


def parse_excel_generation_request(prompt: str, context: Optional[str] = None) -> ParsedExcelRequest:
    """
    Deterministically parses the CURRENT user prompt into structured parameters.
    Extracts row count, column count, domain/dataset type, and distinguishes
    synthetic tabular data from QA test suites.
    """
    clean_p = prompt.strip()

    # 1. Row extraction patterns
    # Handles: "20 rows", "20 data rows", "20 records", "20 student records", "200 test cases", "20-row"
    row_patterns = [
        r"(\d+)\s*(?:data\s*)?rows?\b",
        r"(\d+)\s*(?:student|customer|user|employee|patient|product|sales|tabular|data)?\s*records?\b",
        r"(\d+)\s*(?:[a-zA-Z0-9_\-]+\s*){0,4}test\s*cases?\b",
        r"(\d+)\s*(?:[a-zA-Z0-9_\-]+\s*){0,4}tests?\b",
        r"(\d+)\s*entries\b",
        r"(\d+)[- ]rows?\b",
    ]
    extracted_rows = parse_number_match(clean_p, row_patterns)

    # 2. Column extraction patterns
    # Handles: "30 columns", "30 distinct columns", "30 fields", "30-column", "30 distinct fields"
    col_patterns = [
        r"(\d+)\s*(?:distinct\s*|different\s*|data\s*|relevant\s*)?columns?\b",
        r"(\d+)\s*(?:distinct\s*|different\s*|data\s*)?fields?\b",
        r"(\d+)[- ]columns?\b",
        r"(\d+)[- ]fields?\b",
    ]
    extracted_cols = parse_number_match(clean_p, col_patterns)

    # Check for invalid or excessive requested dimensions
    # E.g. user requested negative or 0 rows/columns or values exceeding configured limits
    raw_number_checks = re.findall(r"(-\d+)\s*(?:rows?|columns?|fields?|records?)", clean_p, re.I)
    if raw_number_checks:
        raise ValueError(f"Invalid dimensions: Requested negative value ({raw_number_checks[0]}) is not supported.")

    if extracted_rows is not None:
        if extracted_rows < MIN_DATA_ROWS:
            raise ValueError(f"Requested row count ({extracted_rows}) must be at least {MIN_DATA_ROWS}.")
        if extracted_rows > MAX_DATA_ROWS:
            raise ValueError(f"Requested row count ({extracted_rows}) exceeds maximum supported limit of {MAX_DATA_ROWS} rows.")

    if extracted_cols is not None:
        if extracted_cols < MIN_DATA_COLS:
            raise ValueError(f"Requested column count ({extracted_cols}) must be at least {MIN_DATA_COLS}.")
        if extracted_cols > MAX_DATA_COLS:
            raise ValueError(f"Requested column count ({extracted_cols}) exceeds maximum supported limit of {MAX_DATA_COLS} columns.")

    # 3. Determine if the request is for QA test cases or synthetic tabular data
    # "Create 100 user registration test cases" -> QA
    # "Create 20 rows and 30 columns of student data" -> Synthetic Tabular Data (NOT QA!)
    has_test_phrase = bool(
        re.search(r"\b(test\s*(?:cases?|suite|scenarios?|data)|qa|test\s*plan|positive\s*and\s*negative|valid\s*and\s*invalid)\b", clean_p, re.I)
    )
    has_explicit_tabular_intent = bool(
        extracted_cols is not None or
        re.search(r"\b(columns?|fields?|spreadsheet|sheet|table|records?)\b", clean_p, re.I) and not re.search(r"\btest\s*cases?\b", clean_p, re.I)
    )

    is_qa = has_test_phrase and not (extracted_cols is not None and not re.search(r"\btest\s*cases?\b", clean_p, re.I))

    # 4. Domain & Dataset Type Detection
    domain = "general"
    app_name = "Custom Spreadsheet"
    prefix = "spreadsheet"

    if re.search(r"\b(student|school|university|academic|college|education|grades?|gpa)\b", clean_p, re.I):
        domain = "student_data"
        app_name = "Student Management System" if is_qa else "Student Information"
        prefix = "student_management_test_data" if is_qa else "student_data"
    elif re.search(r"\b(hospital|patient|doctor|medical|clinic|healthcare)\b", clean_p, re.I):
        domain = "healthcare_data"
        app_name = "Hospital Management System" if is_qa else "Patient Registry"
        prefix = "hospital_management_test_data" if is_qa else "patient_data"
    elif re.search(r"\b(employee|payroll|hr|salary|staff|wages?)\b", clean_p, re.I):
        domain = "employee_data"
        app_name = "Employee & Payroll System" if is_qa else "Employee Directory"
        prefix = "employee_test_data" if is_qa else "employee_data"
    elif re.search(r"\b(customer|client|consumer|crm)\b", clean_p, re.I):
        domain = "customer_data"
        app_name = "Customer Relationship System" if is_qa else "Customer Directory"
        prefix = "customer_test_data" if is_qa else "customer_data"
    elif re.search(r"\b(sales|order|product|checkout|e-?commerce|inventory)\b", clean_p, re.I):
        domain = "sales_data"
        app_name = "E-Commerce System" if is_qa else "Product Sales"
        prefix = "sales_test_data" if is_qa else "sales_data"
    elif re.search(r"\b(registration|signup|sign-up|login|auth)\b", clean_p, re.I):
        domain = "user_registration"
        app_name = "User Registration Application"
        prefix = "application_test_data"
        is_qa = True
    elif is_qa:
        domain = "qa_test_cases"
        app_name = "Application QA Test Suite"
        prefix = "qa_test_data"

    # 5. Determine default rows and columns based on intent and parsed values
    if is_qa:
        data_rows = extracted_rows or 130
        data_columns = extracted_cols or 10
        worksheet_count = 4
        include_summary = True
    else:
        data_rows = extracted_rows or 20
        # Default columns depending on domain
        if extracted_cols is not None:
            data_columns = extracted_cols
        else:
            if domain == "student_data":
                data_columns = 30 if "30" in clean_p else 15
            elif domain in ("customer_data", "employee_data", "sales_data"):
                data_columns = 10
            else:
                data_columns = 7
        worksheet_count = 1
        include_summary = False

    # Multi-sheet check: "multiple worksheets", "3 sheets", "separate sheets"
    sheet_m = re.search(r"(\d+)\s*(?:work)?sheets?\b", clean_p, re.I)
    if sheet_m:
        try:
            worksheet_count = max(1, min(10, int(sheet_m.group(1))))
        except Exception:
            pass
    elif re.search(r"\b(multiple\s*(?:work)?sheets?|separate\s*(?:work)?sheets?)\b", clean_p, re.I):
        worksheet_count = max(worksheet_count, 3)

    # Source determination: document requirements vs web research vs synthetic data
    source = "synthetic_data"
    if context or re.search(r"\b(?:from|in|using)\s+(?:the\s+)?(?:document|pdf|file|requirements)\b", clean_p, re.I):
        source = "document_requirements"
    elif re.search(r"\b(?:search\s+the\s+web|online|internet|research|real[- ]time)\b", clean_p, re.I):
        source = "web_research"

    return ParsedExcelRequest(
        operation="generate_workbook",
        dataset_type=domain,
        data_rows=data_rows,
        data_columns=data_columns,
        worksheet_count=worksheet_count,
        include_summary=include_summary,
        source=source,
        output_format="xlsx",
        is_qa=is_qa,
        application_name=app_name,
        title=app_name,
        prefix=prefix,
        raw_prompt=clean_p
    )
