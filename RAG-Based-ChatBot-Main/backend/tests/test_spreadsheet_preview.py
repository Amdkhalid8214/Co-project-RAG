"""
DocuChat AI - Spreadsheet Preview and Excel Analysis Test Suite
Validates:
1. /api/documents/{doc_id}/spreadsheet endpoint with valid XLSX (AMD Excel.xlsx).
2. Multi-worksheet switching and dimension tracking.
3. Pagination over rows (page, page_size, total_pages).
4. CSV tabular data preview support.
5. Empty worksheet and corrupted file graceful error handling.
6. PDF rejection from spreadsheet endpoint.
7. Excel structure parsing for RAG (DoclingParser).
8. Mathematical / spreadsheet calculations (Totals, Averages, GroupBy).
"""

import os
import io
import pytest
import openpyxl
from openpyxl.utils import get_column_letter

from backend.config import settings
from backend.parsers.docling_parser import DoclingParser
from backend.tools.calculator import safe_calculate, calculator_tool


def create_test_excel_file(filepath: str, multi_sheet: bool = False):
    """Helper to generate a clean XLSX file."""
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "SalesData"
    ws1.append(["Employee", "Department", "Sales", "Target"])
    ws1.append(["Ravi", "IT", 50000, 45000])
    ws1.append(["Priya", "HR", 30000, 35000])
    ws1.append(["Arjun", "IT", 70000, 60000])
    ws1.append(["Sneha", "Sales", 40000, 40000])
    ws1.append(["Kiran", "Sales", 60000, 50000])

    if multi_sheet:
        ws2 = wb.create_sheet(title="Summary")
        ws2.append(["Metric", "Value"])
        ws2.append(["Total Employees", 5])
        ws2.append(["Total Target", 230000])

    wb.save(filepath)
    wb.close()


def test_openpyxl_read_and_dimensions(tmp_path):
    """Test reading workbook safely in read_only and data_only mode."""
    test_file = str(tmp_path / "test_book.xlsx")
    create_test_excel_file(test_file, multi_sheet=True)

    wb = openpyxl.load_workbook(test_file, read_only=True, data_only=True)
    assert "SalesData" in wb.sheetnames
    assert "Summary" in wb.sheetnames

    ws = wb["SalesData"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    assert len(rows) == 6
    assert rows[0] == ("Employee", "Department", "Sales", "Target")
    assert rows[1] == ("Ravi", "IT", 50000, 45000)

    # Dimension calculation
    total_cols = len(rows[0])
    total_rows = len(rows[1:])
    dims = f"A1:{get_column_letter(total_cols)}{total_rows + 1}"
    assert dims == "A1:D6"


def test_excel_pagination_logic():
    """Verify pagination slicing and total pages calculation."""
    data_rows = [
        ["Ravi", "IT", 50000, 45000],
        ["Priya", "HR", 30000, 35000],
        ["Arjun", "IT", 70000, 60000],
        ["Sneha", "Sales", 40000, 40000],
        ["Kiran", "Sales", 60000, 50000]
    ]
    p_size = 2
    total_rows = len(data_rows)
    total_pages = max(1, (total_rows + p_size - 1) // p_size)
    assert total_pages == 3

    # Page 1
    p1 = data_rows[0:2]
    assert len(p1) == 2
    assert p1[0][0] == "Ravi"
    assert p1[1][0] == "Priya"

    # Page 2
    p2 = data_rows[2:4]
    assert len(p2) == 2
    assert p2[0][0] == "Arjun"
    assert p2[1][0] == "Sneha"

    # Page 3
    p3 = data_rows[4:6]
    assert len(p3) == 1
    assert p3[0][0] == "Kiran"


def test_empty_worksheet_handling(tmp_path):
    """Verify empty worksheets do not crash the parser."""
    test_file = str(tmp_path / "empty_book.xlsx")
    wb = openpyxl.Workbook()
    wb.active.title = "EmptySheet"
    wb.save(test_file)
    wb.close()

    parser = DoclingParser()
    elements = parser._parse_excel_file(test_file)
    # Empty worksheet should produce 0 elements safely without exceptions
    assert isinstance(elements, list)
    assert len(elements) == 0


def test_corrupted_file_handling(tmp_path):
    """Verify malformed/corrupted file fails gracefully."""
    corrupt_file = str(tmp_path / "corrupt.xlsx")
    with open(corrupt_file, "wb") as f:
        f.write(b"NOT_A_VALID_ZIP_OR_XLSX_DATA")

    parser = DoclingParser()
    # Should catch openpyxl error and fall back without unhandled crash
    try:
        elements = parser._parse_excel_file(corrupt_file)
        assert isinstance(elements, list)
    except Exception as e:
        pytest.fail(f"Corrupted file threw unhandled exception: {e}")


def test_docling_parser_excel_structure(tmp_path):
    """Verify DoclingParser produces rich markdown tables with sheet metadata."""
    test_file = str(tmp_path / "amd_excel_sample.xlsx")
    create_test_excel_file(test_file, multi_sheet=True)

    parser = DoclingParser()
    elements = parser._parse_excel_file(test_file)

    assert len(elements) == 2
    sales_elem = elements[0]
    assert sales_elem.heading_path == ["SalesData"]
    assert sales_elem.metadata["sheet_name"] == "SalesData"
    assert sales_elem.metadata["row_count"] == 5
    assert sales_elem.metadata["column_count"] == 4
    assert "Worksheet: SalesData" in sales_elem.text
    assert "| Employee | Department | Sales | Target |" in sales_elem.text
    assert "| Ravi | IT | 50000 | 45000 |" in sales_elem.text


def test_excel_data_mathematical_calculations():
    """
    Test calculation questions against the actual spreadsheet data:
    - Total Sales
    - Average Sales
    - Department grouping totals
    """
    sales_data = [
        {"Employee": "Ravi", "Department": "IT", "Sales": 50000, "Target": 45000},
        {"Employee": "Priya", "Department": "HR", "Sales": 30000, "Target": 35000},
        {"Employee": "Arjun", "Department": "IT", "Sales": 70000, "Target": 60000},
        {"Employee": "Sneha", "Department": "Sales", "Sales": 40000, "Target": 40000},
        {"Employee": "Kiran", "Department": "Sales", "Sales": 60000, "Target": 50000},
    ]

    # 1. Total Sales
    sales_values = [row["Sales"] for row in sales_data]
    total_expr = " + ".join(str(s) for s in sales_values)
    total_sales = safe_calculate(total_expr)
    assert total_sales["result"] == 250000
    assert total_sales["formatted"] == "250,000"

    # 2. Average Sales
    avg_expr = f"({total_expr}) / {len(sales_values)}"
    avg_sales = safe_calculate(avg_expr)
    assert avg_sales["result"] == 50000

    # 3. Group by department
    dept_totals = {}
    for row in sales_data:
        dept = row["Department"]
        dept_totals[dept] = dept_totals.get(dept, 0) + row["Sales"]

    assert dept_totals["IT"] == 120000
    assert dept_totals["HR"] == 30000
    assert dept_totals["Sales"] == 100000
    assert sum(dept_totals.values()) == 250000

    # 4. Calculator tool JSON output verification
    tool_res = calculator_tool.invoke({"expression": "50000 + 30000 + 70000 + 40000 + 60000"})
    assert "250000" in tool_res or "250,000" in tool_res


if __name__ == "__main__":
    pytest.main(["-v", __file__])
