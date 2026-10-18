"""
DocuChat AI - Safe Mathematical Calculator Tool
Evaluates mathematical expressions using AST white-listing.
Strictly disallows arbitrary code execution, functions, imports, or variable assignments.
"""
import ast
import operator
import math
import logging
from typing import Dict, Any

logger = logging.getLogger("calculator_tool")

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

SAFE_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "ceil": math.ceil,
    "floor": math.floor,
}

def _eval_node(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")

    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if op_type == ast.Pow and (right > 100 or left > 10000):
            raise ValueError("Exponentiation exceeds safe magnitude limit.")
        return SAFE_OPERATORS[op_type](left, right)

    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        return SAFE_OPERATORS[op_type](_eval_node(node.operand))

    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in SAFE_FUNCTIONS:
                args = [_eval_node(arg) for arg in node.args]
                return SAFE_FUNCTIONS[func_name](*args)
        raise ValueError(f"Unsupported function call in calculation: {getattr(node.func, 'id', 'unknown')}")

    else:
        raise ValueError(f"Unsupported AST node expression: {type(node).__name__}")

def safe_calculate(expression: str) -> Dict[str, Any]:
    """
    Safely calculates arithmetic expressions with AST parsing and validation.
    """
    clean_expr = expression.strip()
    if not clean_expr or len(clean_expr) > 200:
        return {"error": "Expression must be non-empty and under 200 characters."}

    try:
        parsed = ast.parse(clean_expr, mode='eval')
        result = _eval_node(parsed.body)
        return {
            "expression": clean_expr,
            "result": result,
            "formatted": f"{result:,}" if isinstance(result, (int, float)) else str(result)
        }
    except ZeroDivisionError:
        return {"error": "Division by zero is undefined."}
    except Exception as e:
        logger.warning(f"Safe calculator evaluation failed: {e}")
        return {"error": f"Invalid or unsafe arithmetic expression: {str(e)}"}
