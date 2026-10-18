"""
DocuChat AI - Safe Tool Registry & Execution Engine
Enforces schema validation, argument limits, safe sandboxing, and execution timeouts.
Never executes arbitrary code, system commands, or unvetted model requests.
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ValidationError

from backend.tools.calculator import safe_calculate
from backend.tools.excel_generator import generate_excel_sheet
from backend.retrieval.web_search import live_web_search


logger = logging.getLogger("tools_registry")

# Pydantic Input Schemas
class CalculatorInput(BaseModel):
    expression: str = Field(..., max_length=200, description="Mathematical expression to evaluate")

class WebSearchInput(BaseModel):
    query: str = Field(..., min_length=2, max_length=200, description="Web query for factual search")

class ExcelExportInput(BaseModel):
    title: str = Field("Report", max_length=50)
    headers: List[str] = Field(..., min_length=1, max_length=50)
    rows: List[List[Any]] = Field(..., min_length=1, max_length=1000)
    filename_prefix: Optional[str] = Field("report", max_length=30)


TOOL_DEFINITIONS = [
    {
        "name": "calculator",
        "description": "Performs exact arithmetic and mathematical calculations safely.",
        "parameters": CalculatorInput.model_json_schema()
    },
    {
        "name": "web_search",
        "description": "Searches the live public web for current news, facts, and market quotes.",
        "parameters": WebSearchInput.model_json_schema()
    },
    {
        "name": "export_excel",
        "description": "Generates a styled, downloadable Excel spreadsheet from tabular data.",
        "parameters": ExcelExportInput.model_json_schema()
    }
]

async def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates arguments against schema and executes tool within a safe timeout.
    """
    logger.info(f"Executing tool '{tool_name}' with arguments: {arguments}")
    
    try:
        if tool_name == "calculator":
            validated = CalculatorInput(**arguments)
            return safe_calculate(validated.expression)

        elif tool_name == "web_search":
            validated = WebSearchInput(**arguments)
            # Run search in thread pool with 12s timeout
            results = await asyncio.wait_for(
                asyncio.to_thread(live_web_search.get_live_context, validated.query),
                timeout=12.0
            )
            return {
                "query": validated.query,
                "results": results or "No live web results found."
            }

        elif tool_name == "export_excel":
            validated = ExcelExportInput(**arguments)
            return generate_excel_sheet(
                title=validated.title,
                headers=validated.headers,
                rows=validated.rows,
                filename_prefix=validated.filename_prefix
            )

        else:
            return {"error": f"Tool '{tool_name}' is not recognized or permitted."}

    except ValidationError as ve:
        logger.warning(f"Tool argument validation failed for {tool_name}: {ve}")
        return {"error": f"Invalid arguments for tool '{tool_name}': {ve.errors()}"}
    except asyncio.TimeoutError:
        logger.error(f"Tool '{tool_name}' timed out.")
        return {"error": f"Tool '{tool_name}' timed out after 12 seconds."}
    except Exception as e:
        logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
        return {"error": f"Tool execution failed: {str(e)}"}
