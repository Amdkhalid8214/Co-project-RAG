import sys
from pathlib import Path

# Add project root to sys.path
root_dir = str(Path(__file__).resolve().parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pytest
from backend.api.auth import hash_password, verify_password, create_jwt_token, decode_jwt_token

from backend.tools.calculator import safe_calculate
from backend.tools.excel_generator import sanitize_cell_value, generate_excel_sheet

def test_argon2_and_pbkdf2_hashing():
    pwd = "SecurePassword!99"
    hsh, salt = hash_password(pwd)
    assert verify_password(pwd, hsh, salt) is True
    assert verify_password("WrongPassword", hsh, salt) is False

def test_jwt_token_creation_and_decoding():
    token = create_jwt_token(user_id="user_123", username="testuser", role="user")
    assert isinstance(token, str)
    payload = decode_jwt_token(token)
    assert payload is not None
    assert payload["sub"] == "user_123"
    assert payload["username"] == "testuser"
    assert payload["role"] == "user"

def test_safe_calculator_ast():
    # Valid mathematical operations
    res = safe_calculate("2 + 2 * 10")
    assert res["result"] == 22

    res_pow = safe_calculate("2 ** 8")
    assert res_pow["result"] == 256

    res_fn = safe_calculate("sqrt(144) + abs(-10)")
    assert res_fn["result"] == 22.0

    # Division by zero
    res_div0 = safe_calculate("100 / 0")
    assert "error" in res_div0

    # Malicious injection attempts - must be rejected by AST parser
    res_inject1 = safe_calculate("__import__('os').system('ls')")
    assert "error" in res_inject1

    res_inject2 = safe_calculate("eval('1+1')")
    assert "error" in res_inject2

    res_inject3 = safe_calculate("open('/etc/passwd').read()")
    assert "error" in res_inject3

def test_excel_formula_injection_defense():
    # Dangerous formula injection triggers
    assert sanitize_cell_value("=1+1") == "'=1+1"
    assert sanitize_cell_value("+cmd|'/c calc'!A0") == "'+cmd|'/c calc'!A0"
    assert sanitize_cell_value("-5*5") == "'-5*5"
    assert sanitize_cell_value("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert sanitize_cell_value("\tDangerous") == "'\tDangerous"

    # Safe cell values
    assert sanitize_cell_value("Quarterly Revenue") == "Quarterly Revenue"
    assert sanitize_cell_value(12345) == 12345
    assert sanitize_cell_value(99.9) == 99.9

def test_excel_generation_produces_file():
    headers = ["Metric", "Q1", "Q2"]
    rows = [["Sales", 1000, 1500], ["Profit", 250, 400]]
    result = generate_excel_sheet(title="Financials", headers=headers, rows=rows, filename_prefix="test_fin")
    assert result["row_count"] == 2
    assert result["column_count"] == 3
    assert result["filename"].endswith(".xlsx")
    assert "download_url" in result
