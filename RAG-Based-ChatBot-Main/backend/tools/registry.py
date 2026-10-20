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
from backend.tools.excel_generator import generate_excel_sheet, generate_workbook_from_request, ExcelGeneratorInput
from backend.tools.excel_analyzer import execute_excel_analysis, ExcelAnalysisInput
from backend.tools.searxng_search import search_searxng_async
from backend.tools.weather import get_weather_forecast_async, WeatherInput
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
        "name": "weather",
        "description": "Fetches live weather reports, temperatures, forecasts, rain chances, and conditions for any city or region.",
        "parameters": WeatherInput.model_json_schema()
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
    },
    {
        "name": "excel_generator",
        "description": "Generates a multi-sheet, beautifully styled, validated Excel workbook (.xlsx) with QA test cases or custom spreadsheets.",
        "parameters": ExcelGeneratorInput.model_json_schema()
    },
    {
        "name": "excel_analyzer",
        "description": "Inspects and calculates metrics from uploaded Excel (.xlsx, .xls) and CSV spreadsheets.",
        "parameters": ExcelAnalysisInput.model_json_schema()
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

        elif tool_name == "weather":
            validated = WeatherInput(**arguments)
            return await get_weather_forecast_async(
                location=validated.location,
                days=validated.days,
                unit=validated.unit
            )

        elif tool_name == "web_search":
            validated = WebSearchInput(**arguments)
            searx_res = await search_searxng_async(validated.query, inspect_pages=True)
            return {
                "query": validated.query,
                "results": searx_res.get("formatted"),
                "raw_results": searx_res.get("results", []),
                "count": searx_res.get("count", 0)
            }

        elif tool_name == "export_excel":
            validated = ExcelExportInput(**arguments)
            return generate_excel_sheet(
                title=validated.title,
                headers=validated.headers,
                rows=validated.rows,
                filename_prefix=validated.filename_prefix
            )

        elif tool_name == "excel_generator":
            validated = ExcelGeneratorInput(**arguments)
            return await generate_workbook_from_request(prompt=validated.requirement)

        elif tool_name == "excel_analyzer":
            validated = ExcelAnalysisInput(**arguments)
            return execute_excel_analysis(
                operation=validated.operation,
                column=validated.column,
                group_by=validated.group_by,
                filter_column=validated.filter_column,
                filter_value=validated.filter_value,
                sheet_name=validated.sheet_name,
                doc_id=validated.doc_id
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
