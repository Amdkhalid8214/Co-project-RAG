"""
DocuChat AI - Safe Mathematical Calculator Tool
Evaluates mathematical expressions using AST white-listing and strict validation.
Disallows arbitrary code execution, imports, file access, or variable assignments.
Provides a LangChain @tool interface for automatic tool calling by LLMs.
"""
import ast
import operator
import math
import re
import json
import logging
from typing import Dict, Any, Union
from pydantic import BaseModel, Field
from langchain_core.tools import tool

logger = logging.getLogger("calculator_tool")

# Whitelist of safe operators
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Whitelist of safe mathematical functions
SAFE_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "ceil": math.ceil,
    "floor": math.floor,
}

# Maximum magnitude boundaries for exponentiation and numbers
MAX_EXPONENT = 1000
MAX_BASE_FOR_LARGE_EXP = 10000
MAX_NUMERIC_MAGNITUDE = 1e100


def preprocess_expression(expression: str) -> str:
    """
    Normalizes common math notation (e.g. '×' -> '*', '÷' -> '/', '^' -> '**', '18% of 7500')
    into standard Python arithmetic syntax while preserving strict safety.
    """
    if not expression or not isinstance(expression, str):
        return ""

    s = expression.strip()

    # Normalize unicode symbols
    s = s.replace("×", "*").replace("÷", "/")

    # Exponentiation notation: '^' to '**'
    # Replace '^' with '**'
    s = s.replace("^", "**")

    # Percentage transformations:
    # 1. 'X% of Y' -> '(X / 100) * Y'
    s = re.sub(
        r"(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)",
        r"(\1 / 100) * \2",
        s,
        flags=re.IGNORECASE
    )

    # 2. 'X%' followed by operator or end of string: '18% * 7500' -> '(18 / 100) * 7500'
    s = re.sub(
        r"(\d+(?:\.\d+)?)\s*%(?!\s*[a-zA-Z0-9_])",
        r"(\1 / 100)",
        s
    )

    return s.strip()


def _eval_node(node: ast.AST) -> Union[int, float]:
    """
    Recursively and safely evaluates an AST node using an explicit whitelist.
    Raises ValueError or ZeroDivisionError if any unsupported or unsafe node is found.
    """
    if isinstance(node, ast.Constant):
        # Strict type check: Only int or float constants are permitted
        if type(node.value) in (int, float):
            if abs(node.value) > MAX_NUMERIC_MAGNITUDE:
                raise ValueError("Number exceeds safe numeric bounds.")
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")

    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")

        left = _eval_node(node.left)
        right = _eval_node(node.right)

        # Division by zero guards
        if op_type in (ast.Div, ast.FloorDiv, ast.Mod):
            if right == 0:
                raise ZeroDivisionError("Division by zero is undefined.")

        # Exponentiation safety guards to prevent denial-of-service / CPU freezing
        if op_type == ast.Pow:
            if abs(right) > MAX_EXPONENT:
                raise ValueError(f"Exponent exceeds safe limit (maximum allowed exponent is {MAX_EXPONENT}).")
            if abs(left) > MAX_BASE_FOR_LARGE_EXP and right > 50:
                raise ValueError("Exponentiation exceeds safe magnitude limit.")

        try:
            result = SAFE_OPERATORS[op_type](left, right)
            if isinstance(result, (int, float)) and abs(result) > MAX_NUMERIC_MAGNITUDE:
                raise ValueError("Result exceeds maximum safe numeric magnitude.")
            return result
        except OverflowError:
            raise ValueError("Calculation resulted in numerical overflow.")

    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        return SAFE_OPERATORS[op_type](_eval_node(node.operand))

    elif isinstance(node, ast.Call):
        # Only allow explicitly whitelisted mathematical functions
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in SAFE_FUNCTIONS:
                args = [_eval_node(arg) for arg in node.args]
                return SAFE_FUNCTIONS[func_name](*args)
        raise ValueError(f"Unsupported function call: {getattr(node.func, 'id', 'unknown')}")

    else:
        # Strictly reject any other AST node (Attributes, Imports, Subscripts, Lambdas, Dicts, etc.)
        raise ValueError(f"Unsupported or unsafe expression element: {type(node).__name__}")


def safe_calculate(expression: str) -> Dict[str, Any]:
    """
    Safely calculates arithmetic expressions with AST parsing and strict validation.
    Returns a structured dictionary with expression and result, or controlled error.
    """
    if not expression or not isinstance(expression, str):
        return {"error": "Expression must be a non-empty string."}

    raw = expression.strip()
    if not raw:
        return {"error": "Expression must be non-empty."}

    if len(raw) > 200:
        return {"error": "Expression exceeds maximum length of 200 characters."}

    # Ensure expression contains at least some mathematical content (digit or math function)
    if not any(c.isdigit() for c in raw) and not any(fn in raw for fn in SAFE_FUNCTIONS):
        return {"error": "Expression must contain numbers to calculate."}

    try:
        clean_expr = preprocess_expression(raw)
        parsed = ast.parse(clean_expr, mode='eval')
        raw_result = _eval_node(parsed.body)

        # Normalize floating point representations (e.g. 50.0 -> 50 if exact integer)
        if isinstance(raw_result, float) and raw_result.is_integer() and abs(raw_result) < 1e15:
            result = int(raw_result)
        else:
            result = raw_result

        # Format number with thousands separator if appropriate
        formatted = f"{result:,}" if isinstance(result, (int, float)) else str(result)

        return {
            "expression": raw,
            "result": result,
            "formatted": formatted
        }
    except ZeroDivisionError:
        return {"error": "Division by zero is undefined."}
    except SyntaxError as se:
        logger.warning(f"Malformed arithmetic expression syntax: {raw} ({se})")
        return {"error": f"Malformed mathematical expression: {raw}"}
    except ValueError as ve:
        logger.warning(f"Safe calculator validation rejected: {raw} ({ve})")
        return {"error": str(ve)}
    except Exception as e:
        logger.warning(f"Safe calculator evaluation failed: {e}")
        return {"error": f"Invalid or unsafe arithmetic expression: {str(e)}"}


# Pydantic input schema for LangChain tool
class CalculatorInput(BaseModel):
    expression: str = Field(
        ...,
        description="The mathematical arithmetic expression to evaluate, such as '43235 * 254', '1250 * 48', '(125 + 75) / 4', or '18% of 7500'."
    )


@tool("calculator", args_schema=CalculatorInput)
def calculator_tool(expression: str) -> str:
    """Useful for evaluating mathematical and arithmetic calculations, including addition,
    subtraction, multiplication, division, percentages (e.g. '18% of 7500'), exponentiation (e.g. '2^10'),
    parentheses, negative numbers, and decimals.
    Input must be a valid mathematical expression string.
    Returns a JSON string containing the calculation result or error.
    """
    res = safe_calculate(expression)
    return json.dumps(res)


# Alias for convenience
calculate = calculator_tool
