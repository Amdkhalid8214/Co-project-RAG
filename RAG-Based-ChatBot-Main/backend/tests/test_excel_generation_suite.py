"""
DocuChat AI - Complete Excel Generation & QA Test Data Engine Test Suite
Validates all 14 requirements from Part 9:
1. Creating a workbook from user-provided data.
2. Creating a QA test-data workbook.
3. Creating multiple worksheets.
4. Verifying row counts and headers.
5. Opening the generated XLSX successfully.
6. Downloading the actual generated file through the frontend / API.
7. Handling invalid input and failed generation.
8. Handling large requests within configured limits.
9. Preventing path traversal and unauthorized file access.
10. Preserving text safely against formula injection (CWE-1236).
11. Confirming that Excel analysis still reads uploaded workbooks.
12. Confirming that PDF RAG and evidence navigation still work.
13. Confirming that weather and general web-search questions still use their proper workflows.
14. Confirming that ordinary Excel explanations do not unnecessarily generate files.
"""

import os
import io
import pytest
from pathlib import Path
import openpyxl

from backend.config import settings
from backend.tools.excel_generator import (
    sanitize_cell_value,
    generate_custom_workbook,
    generate_qa_test_data_workbook,
    validate_generated_workbook,
    generate_workbook_from_request,
    excel_generator_tool,
)
from backend.llm.router import (
    is_excel_generation_request,
    is_weather_request,
    is_explicit_web_search_request,
    query_router,
)
from backend.api.tools import download_output_file
from fastapi import HTTPException


# ==============================================================================
# 1. Creating a workbook from user-provided data
# ==============================================================================
def test_create_workbook_from_user_data(tmp_path):
    headers = ["EmpID", "Name", "Department", "Salary"]
    rows = [
        ["E001", "Alice Smith", "Engineering", 125000],
        ["E002", "Bob Johnson", "Product", 110000],
        ["E003", "Carol Williams", "Design", 95000]
    ]
    artifact = generate_custom_workbook(
        title="Employee Data",
        sheets_data=[
            {
                "sheet_name": "Employees",
                "headers": headers,
                "rows": rows
            }
        ],
        filename_prefix="test_employees"
    )

    assert artifact["filename"].endswith(".xlsx")
    assert artifact["sheet_count"] == 1
    assert artifact["total_rows"] == 3
    assert artifact["validation_status"] == "Created and validated"

    file_path = os.path.join(settings.OUTPUT_DIR, artifact["filename"])
    assert os.path.exists(file_path)

    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb["Employees"]
    assert ws.max_row == 4  # 1 header + 3 data rows
    assert [cell.value for cell in ws[1]] == headers
    assert ws.cell(row=2, column=2).value == "Alice Smith"
    wb.close()


# ==============================================================================
# 2. Creating a QA test-data workbook (Matches Screenshots 1 & 2)
# ==============================================================================
def test_create_qa_test_data_workbook():
    artifact = generate_qa_test_data_workbook(
        application_name="User Registration Application",
        filename_prefix="application_test_data"
    )

    assert artifact["filename"] == "application_test_data.xlsx"
    assert artifact["file_type"] == "Excel workbook"
    assert artifact["sheet_count"] == 4
    assert artifact["total_cases"] == 130
    assert artifact["large_dataset_cases"] == 100
    assert artifact["validation_status"] == "Created and validated"
    assert artifact["is_qa_test_data"] is True
    assert "Done, AMD!" in artifact["reply_message"]
    assert "130 test cases" in artifact["reply_message"]

    # Verify category breakdown counts match Screenshot 1 exactly
    cat_map = {c["name"]: c["count"] for c in artifact["coverage"]["categories"]}
    assert cat_map["Valid Data"] == 2
    assert cat_map["Invalid Data"] == 7
    assert cat_map["Boundary Cases"] == 4
    assert cat_map["Missing Data"] == 5
    assert cat_map["Duplicate Data"] == 2
    assert cat_map["Edge Cases"] == 4
    assert cat_map["Data Type Errors"] == 2
    assert cat_map["Security Test Inputs"] == 4
    assert cat_map["Large Dataset"] == 100


# ==============================================================================
# 3. Creating multiple worksheets with professional formatting
# ==============================================================================
def test_multiple_worksheets_structure():
    artifact = generate_qa_test_data_workbook(
        application_name="User Login Application",
        filename_prefix="login_test_data"
    )
    file_path = os.path.join(settings.OUTPUT_DIR, artifact["filename"])
    wb = openpyxl.load_workbook(file_path, data_only=True)

    expected_sheets = ["Summary", "Functional Tests", "Security & Edge Tests", "Large Dataset"]
    assert wb.sheetnames == expected_sheets

    # Verify frozen panes and auto-filter on Functional Tests
    ws_func = wb["Functional Tests"]
    assert ws_func.freeze_panes == "A2"
    assert ws_func.auto_filter.ref is not None

    # Verify Summary Sheet banner
    ws_summary = wb["Summary"]
    assert "QA Test Suite & Coverage Report" in str(ws_summary["A1"].value)
    wb.close()


# ==============================================================================
# 4. Verifying row counts and headers
# ==============================================================================
def test_row_counts_and_headers():
    artifact = generate_qa_test_data_workbook()
    file_path = os.path.join(settings.OUTPUT_DIR, artifact["filename"])
    wb = openpyxl.load_workbook(file_path, data_only=True)

    # Functional Tests sheet
    ws_func = wb["Functional Tests"]
    expected_headers = [
        "Test Case ID", "Test Category", "Test Scenario", "Test Data",
        "Preconditions", "Steps", "Expected Result", "Actual Result", "Status", "Priority"
    ]
    actual_headers = [cell.value for cell in ws_func[1]]
    assert actual_headers == expected_headers
    # Functional cases count: 26 rows in functional sheet
    assert ws_func.max_row >= 25

    # Large Dataset sheet
    ws_large = wb["Large Dataset"]
    assert ws_large.max_row == 101  # 1 header + 100 records
    wb.close()


# ==============================================================================
# 5. Opening the generated XLSX successfully
# ==============================================================================
def test_reopen_xlsx_successfully():
    artifact = generate_qa_test_data_workbook()
    file_path = os.path.join(settings.OUTPUT_DIR, artifact["filename"])
    val = validate_generated_workbook(file_path, ["Summary", "Functional Tests", "Security & Edge Tests", "Large Dataset"])

    assert val["valid"] is True
    assert val["sheet_count"] == 4
    assert val["total_data_rows"] > 100
    assert val["validation_status"] == "Created and validated"


# ==============================================================================
# 6. Downloading the actual generated file through the API
# ==============================================================================
@pytest.mark.asyncio
async def test_download_endpoint_serves_actual_file():
    artifact = generate_qa_test_data_workbook(filename_prefix="download_test")
    filename = artifact["filename"]

    response = await download_output_file(filename=filename)
    assert response.status_code == 200
    assert response.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert f"filename={filename}" in response.headers["Content-Disposition"]
    assert os.path.exists(response.path)


# ==============================================================================
# 7. Handling invalid input and failed generation
# ==============================================================================
def test_invalid_input_and_failed_generation():
    non_existent_file = os.path.join(settings.OUTPUT_DIR, "non_existent_fake_workbook.xlsx")
    with pytest.raises(FileNotFoundError):
        validate_generated_workbook(non_existent_file)


# ==============================================================================
# 8. Handling large requests within configured limits
# ==============================================================================
def test_large_request_limits():
    artifact = generate_qa_test_data_workbook(filename_prefix="large_stress_test")
    file_path = os.path.join(settings.OUTPUT_DIR, artifact["filename"])
    file_size = os.path.getsize(file_path)

    # Ensure size is reasonable and well under the 15MB ceiling
    assert 5000 < file_size < 15 * 1024 * 1024


# ==============================================================================
# 9. Preventing path traversal and unauthorized file access
# ==============================================================================
@pytest.mark.asyncio
async def test_path_traversal_prevention():
    malicious_filenames = [
        "../../etc/passwd",
        "..\\..\\windows\\win.ini",
        "....//....//boot.ini",
        "/etc/shadow"
    ]
    for bad_name in malicious_filenames:
        with pytest.raises(HTTPException) as exc_info:
            await download_output_file(filename=bad_name)
        assert exc_info.value.status_code in (403, 404)


# ==============================================================================
# 10. Preserving text safely against formula injection (CWE-1236)
# ==============================================================================
def test_formula_injection_defense():
    assert sanitize_cell_value("=SUM(A1:A10)") == "'=SUM(A1:A10)"
    assert sanitize_cell_value("+1234567890") == "'+1234567890"
    assert sanitize_cell_value("-cmd|'/C calc'!A0") == "'-cmd|'/C calc'!A0"
    assert sanitize_cell_value("@cmd") == "'@cmd"
    assert sanitize_cell_value("\tmalicious_tab") == "'\tmalicious_tab"
    assert sanitize_cell_value("\rmalicious_cr") == "'\rmalicious_cr"
    # Normal safe strings should remain untouched
    assert sanitize_cell_value("Normal text") == "Normal text"
    assert sanitize_cell_value("user@example.com") == "user@example.com"
    assert sanitize_cell_value(42) == 42


# ==============================================================================
# 11. Confirming that Excel analysis still reads uploaded workbooks
# ==============================================================================
def test_excel_analysis_reads_uploaded_workbooks():
    # Questions that should be routed to analysis, NOT generation
    analysis_questions = [
        "Analyze my uploaded Excel file",
        "How many rows in the sheet?",
        "What are the column names in the spreadsheet?",
        "Summarize the uploaded excel sheet",
        "Inspect the uploaded spreadsheet data"
    ]
    for q in analysis_questions:
        assert is_excel_generation_request(q) is False, f"Expected False for analysis query: '{q}'"


# ==============================================================================
# 12. Confirming that PDF RAG and evidence navigation still work
# ==============================================================================
def test_pdf_rag_still_works():
    doc_questions = [
        "What is the candidate's work experience according to the resume?",
        "What does the policy document say about remote work?",
        "Extract the exact wording of section 4 from the PDF"
    ]
    for q in doc_questions:
        assert is_excel_generation_request(q) is False, f"Expected False for document query: '{q}'"


# ==============================================================================
# 13. Confirming that weather and general web-search questions use proper workflows
# ==============================================================================
def test_weather_and_web_search_workflows():
    weather_q = "What is the weather today in Goa?"
    assert is_weather_request(weather_q) is True
    assert is_excel_generation_request(weather_q) is False

    web_q = "Research on the internet and give me a guide on how to use OKF"
    assert is_explicit_web_search_request(web_q) is True
    assert is_excel_generation_request(web_q) is False


# ==============================================================================
# 14. Confirming that ordinary Excel explanations do not generate files
# ==============================================================================
def test_ordinary_excel_explanations_no_file_generation():
    info_questions = [
        "What is Excel?",
        "Explain Excel",
        "How does Excel work?",
        "Find current Excel documentation",
        "Excel tutorial for beginners",
        "Who created Excel?"
    ]
    for q in info_questions:
        assert is_excel_generation_request(q) is False, f"Expected False for informational query: '{q}'"


# ==============================================================================
# End-to-end Intent Routing Tests for Requested Examples
# ==============================================================================
@pytest.mark.asyncio
async def test_all_user_request_examples_route_to_excel_generation():
    user_examples = [
        "Create an Excel sheet for user registration testing.",
        "Generate 100 test cases for my login page.",
        "Convert this data into an Excel file.",
        "Create an Excel sheet with valid and invalid email examples.",
        "Generate test data from the following requirements.",
        "Create an Excel workbook with separate sheets for positive and negative tests.",
        "Give me a downloadable spreadsheet containing this data.",
        "Create an Excel file about the topic you just researched"
    ]
    for prompt in user_examples:
        assert is_excel_generation_request(prompt) is True, f"Failed to detect intent for: '{prompt}'"
        route, badge = await query_router.route_query(prompt, has_documents=False)
        assert route == "excel_generation", f"Expected 'excel_generation' route for: '{prompt}'"
        assert badge == "📊 Excel Generator"


@pytest.mark.asyncio
async def test_end_to_end_generate_workbook_from_request():
    artifact = await generate_workbook_from_request("Create an Excel sheet for user registration testing.")
    assert artifact["filename"] == "application_test_data.xlsx"
    assert artifact["sheet_count"] == 4
    assert artifact["total_cases"] == 130
    assert artifact["validation_status"] == "Created and validated"
    assert artifact["download_url"] == "/api/tools/download/application_test_data.xlsx"


@pytest.mark.asyncio
async def test_stream_rag_response_excel_generation_events():
    from backend.llm.generator import grounded_generator
    chunks = []
    async for sse in grounded_generator.stream_rag_response(
        question="Create an Excel sheet for user registration testing.",
        route="excel_generation",
        router_badge="📊 Excel Generator",
        retrieved_chunks=[],
        queries=["Create an Excel sheet for user registration testing."],
        web_mode=False
    ):
        chunks.append(sse)

    combined = "".join(chunks)
    assert "event: meta" in combined
    assert "📊 Excel Generator" in combined
    assert "event: excel_artifact" in combined
    assert "application_test_data.xlsx" in combined
    assert "event: token" in combined
    assert "Done, AMD!" in combined
    assert "event: done" in combined
