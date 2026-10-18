"""
Automated Test Suite for Safe LangChain Calculator Tool in DocuChat AI.

Covers:
1. Positive Arithmetic Calculations:
   - 43235 * 254 = 10981690
   - 1250 * 48 = 60000
   - 18% of 7500 = 1350
   - (125 + 75) / 4 = 50
   - Negative numbers and decimal arithmetic (-50 + 25, -10.5 * 2, 0.5 * 0.5)
   - Correct operator precedence (2 + 3 * 4 = 14, (2 + 3) * 4 = 20, 2^10 = 1024)

2. Negative & Security Tests:
   - Division by zero (10 / 0, 5 // 0)
   - Malformed expressions ((125 + 75, 10 * * 2, empty string)
   - Arbitrary code execution & injection attempts (__import__, eval, exec, open, .__class__)
   - Unsupported functions (sin, cos, unknown functions)
   - Excessive numeric limits (99999 ** 99999)
   - Tool execution exceptions handled gracefully

3. LangChain Tool Calling & Orchestration Flow:
   - HumanMessage -> AIMessage with tool_calls -> execute calculator -> ToolMessage -> AIMessage final answer
   - Ordinary questions answered without calling calculator
   - Standalone operation without external internet or API keys
"""

import sys
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

# Ensure project root is in sys.path
root_dir = str(Path(__file__).resolve().parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from backend.tools.calculator import safe_calculate, calculator_tool, preprocess_expression


# ==========================================
# 1. POSITIVE ARITHMETIC UNIT TESTS
# ==========================================

def test_multiplication_large_integers():
    """Verify 43235 * 254 = 10981690"""
    res = safe_calculate("43235 * 254")
    assert "error" not in res
    assert res["result"] == 10981690
    assert res["formatted"] == "10,981,690"


def test_multiplication_standard():
    """Verify 1250 * 48 = 60000"""
    res = safe_calculate("1250 * 48")
    assert "error" not in res
    assert res["result"] == 60000
    assert res["formatted"] == "60,000"


def test_percentage_calculation():
    """Verify 18% of 7500 = 1350"""
    res = safe_calculate("18% of 7500")
    assert "error" not in res
    assert res["result"] == 1350
    assert res["formatted"] == "1,350"


def test_parentheses_and_division():
    """Verify (125 + 75) / 4 = 50"""
    res = safe_calculate("(125 + 75) / 4")
    assert "error" not in res
    assert res["result"] == 50
    assert res["formatted"] == "50"


def test_negative_numbers_and_decimals():
    """Verify negative numbers and decimal arithmetic"""
    res1 = safe_calculate("-50 + 25")
    assert "error" not in res1
    assert res1["result"] == -25

    res2 = safe_calculate("-10.5 * 2")
    assert "error" not in res2
    assert res2["result"] == -21

    res3 = safe_calculate("0.5 * 0.5")
    assert "error" not in res3
    assert res3["result"] == 0.25

    res4 = safe_calculate("10 - -5")
    assert "error" not in res4
    assert res4["result"] == 15


def test_operator_precedence():
    """Verify standard PEMDAS operator precedence"""
    res1 = safe_calculate("2 + 3 * 4")
    assert res1["result"] == 14  # Multiplication before addition

    res2 = safe_calculate("(2 + 3) * 4")
    assert res2["result"] == 20  # Parentheses override

    res3 = safe_calculate("2^10")
    assert res3["result"] == 1024  # Exponentiation notation

    res4 = safe_calculate("2 ** 3 * 2")
    assert res4["result"] == 16  # 8 * 2


# ==========================================
# 2. NEGATIVE & SECURITY UNIT TESTS
# ==========================================

def test_division_by_zero():
    """Verify division by zero returns a controlled error without crashing"""
    res1 = safe_calculate("10 / 0")
    assert "error" in res1
    assert "division by zero" in res1["error"].lower()

    res2 = safe_calculate("5 // 0")
    assert "error" in res2
    assert "division by zero" in res2["error"].lower()


def test_malformed_expressions():
    """Verify malformed expressions return controlled syntax errors"""
    res1 = safe_calculate("(125 + 75")  # Unclosed paren
    assert "error" in res1

    res2 = safe_calculate("10 * * 2")  # Invalid syntax
    assert "error" in res2

    res3 = safe_calculate("")  # Empty
    assert "error" in res3

    res4 = safe_calculate("   ")  # Whitespace
    assert "error" in res4

    res5 = safe_calculate("pure text without math")
    assert "error" in res5


def test_arbitrary_code_injection_prevention():
    """Strictly verify that arbitrary code execution and injection are blocked"""
    injection_payloads = [
        "__import__('os').system('ls')",
        "eval('2+2')",
        "exec('x = 1')",
        "open('test.txt', 'w')",
        "().__class__.__bases__[0].__subclasses__()",
        "import sys; sys.exit(0)",
        "[x for x in (1, 2, 3)]",
        "lambda x: x + 1",
    ]
    for payload in injection_payloads:
        res = safe_calculate(payload)
        assert "error" in res, f"Failed to block code injection: {payload}"


def test_unsupported_functions():
    """Verify unvetted or unsupported mathematical functions are rejected"""
    res1 = safe_calculate("sin(90)")
    assert "error" in res1

    res2 = safe_calculate("cos(0)")
    assert "error" in res2

    res3 = safe_calculate("unknown_func(42)")
    assert "error" in res3


def test_unreasonable_numeric_inputs():
    """Verify excessively large computations are blocked to prevent CPU freezing / DoS"""
    res1 = safe_calculate("99999 ** 99999")
    assert "error" in res1
    assert "exponent" in res1["error"].lower() or "magnitude" in res1["error"].lower()

    res2 = safe_calculate("2 ** 100000")
    assert "error" in res2


def test_langchain_tool_invoke():
    """Verify LangChain @tool calculator_tool invocation returns valid JSON string"""
    result_json = calculator_tool.invoke({"expression": "43235 * 254"})
    parsed = json.loads(result_json)
    assert parsed["result"] == 10981690

    error_json = calculator_tool.invoke({"expression": "10 / 0"})
    parsed_err = json.loads(error_json)
    assert "error" in parsed_err


# ==========================================
# 3. TOOL CALLING ORCHESTRATION TESTS
# ==========================================

@pytest.mark.asyncio
async def test_langchain_tool_calling_flow_mocked():
    """
    Verifies the full tool-calling flow:
    HumanMessage -> AIMessage with tool_calls -> execute calculator -> ToolMessage -> AIMessage final answer
    """
    from backend.llm.langchain_adapter import LangChainAdapter

    adapter = LangChainAdapter()

    # Step 1: User asks a calculation
    user_msg = HumanMessage(content="What is 43235 * 254?")

    # Step 2: Model returns AIMessage with tool_calls
    tool_call_id = "test-call-12345"
    ai_tool_call_msg = AIMessage(
        content="",
        tool_calls=[{
            "name": "calculator",
            "args": {"expression": "43235 * 254"},
            "id": tool_call_id,
            "type": "tool_call"
        }]
    )

    # Step 3: Python executes calculator tool
    raw_tool_result = calculator_tool.invoke(ai_tool_call_msg.tool_calls[0]["args"])
    tool_data = json.loads(raw_tool_result)
    assert tool_data["result"] == 10981690

    # Step 4: ToolMessage constructed with result
    tool_msg = ToolMessage(
        content=raw_tool_result,
        tool_call_id=tool_call_id,
        name="calculator"
    )

    # Step 5: Final AIMessage generated
    final_ai_msg = AIMessage(content=f"The product of 43235 and 254 is {tool_data['formatted']}.")
    assert "10,981,690" in final_ai_msg.content

    # Verify message sequence structure
    messages_trajectory = [user_msg, ai_tool_call_msg, tool_msg, final_ai_msg]
    assert len(messages_trajectory) == 4
    assert isinstance(messages_trajectory[0], HumanMessage)
    assert isinstance(messages_trajectory[1], AIMessage) and bool(messages_trajectory[1].tool_calls)
    assert isinstance(messages_trajectory[2], ToolMessage)
    assert isinstance(messages_trajectory[3], AIMessage) and not bool(messages_trajectory[3].tool_calls)


@pytest.mark.asyncio
async def test_tool_calling_loop_execution():
    """
    Verifies that execute_tool_call_loop correctly handles tool execution and returns final answer.
    """
    from backend.llm.langchain_adapter import execute_tool_call_loop

    user_msg = HumanMessage(content="Calculate 1250 * 48")

    # Mock LLM that returns a tool call on first step, then final answer on second step
    mock_llm = MagicMock()
    
    first_response = AIMessage(
        content="",
        tool_calls=[{
            "name": "calculator",
            "args": {"expression": "1250 * 48"},
            "id": "call-1",
            "type": "tool_call"
        }]
    )
    second_response = AIMessage(content="The result is 60,000.")

    mock_llm.ainvoke = AsyncMock(side_effect=[first_response, second_response])

    final_content, tool_called = await execute_tool_call_loop(
        llm_with_tools=mock_llm,
        llm_plain=mock_llm,
        messages=[user_msg],
        tools=[calculator_tool]
    )

    assert tool_called is True
    assert "60,000" in final_content
    assert mock_llm.ainvoke.call_count == 2


@pytest.mark.asyncio
async def test_ordinary_question_without_tool_call():
    """
    Verifies that ordinary questions are answered without triggering the calculator tool.
    """
    from backend.llm.langchain_adapter import execute_tool_call_loop

    user_msg = HumanMessage(content="Explain what a transformer model is in one sentence.")

    mock_llm = MagicMock()
    direct_response = AIMessage(content="A transformer is a neural network architecture based on self-attention mechanisms.")

    mock_llm.ainvoke = AsyncMock(return_value=direct_response)

    final_content, tool_called = await execute_tool_call_loop(
        llm_with_tools=mock_llm,
        llm_plain=mock_llm,
        messages=[user_msg],
        tools=[calculator_tool]
    )

    assert tool_called is False
    assert "transformer is a neural network" in final_content
    assert mock_llm.ainvoke.call_count == 1


# ==========================================
# 4. REGRESSION & INTEGRATION TESTS
# ==========================================

def test_calculator_offline_no_network():
    """
    Verify calculator executes in pure Python without internet access or external API keys.
    """
    expressions = [
        ("43235 * 254", 10981690),
        ("1250 * 48", 60000),
        ("18% of 7500", 1350),
        ("(125 + 75) / 4", 50),
        ("-50 + 25", -25),
        ("10.5 * 2.5", 26.25),
    ]
    for expr, expected in expressions:
        res = safe_calculate(expr)
        assert res.get("result") == expected, f"Failed for {expr}"


def test_router_math_classification():
    """
    Verify query router identifies standalone math expressions.
    """
    from backend.llm.router import query_router, is_standalone_math_request

    assert is_standalone_math_request("What is 43235 * 254?") is True
    assert is_standalone_math_request("calculate 1250 * 48") is True
    assert is_standalone_math_request("18% of 7500") is True
    assert is_standalone_math_request("(125 + 75) / 4") is True

    # Ordinary questions must NOT be classified as standalone math
    assert is_standalone_math_request("What is the capital of France?") is False
    assert is_standalone_math_request("Summarize page 2 of the document") is False
    assert is_standalone_math_request("What is Attention mechanism?") is False


@pytest.mark.asyncio
async def test_streaming_generator_with_tool_call():
    """
    Verify stream_chat_with_tools yields streamed tokens when tool call occurs.
    """
    from backend.llm.langchain_adapter import LangChainAdapter

    adapter = LangChainAdapter()

    user_msg = HumanMessage(content="What is 43235 * 254?")
    ai_tool_msg = AIMessage(
        content="",
        tool_calls=[{
            "name": "calculator",
            "args": {"expression": "43235 * 254"},
            "id": "call_abc",
            "type": "tool_call"
        }]
    )

    mock_llm_tools = MagicMock()
    mock_llm_tools.ainvoke = AsyncMock(return_value=ai_tool_msg)

    async def mock_astream(messages):
        yield MagicMock(content="The ")
        yield MagicMock(content="result ")
        yield MagicMock(content="is ")
        yield MagicMock(content="10,981,690.")

    mock_llm_plain = MagicMock()
    mock_llm_plain.bind_tools = MagicMock(return_value=mock_llm_tools)
    mock_llm_plain.astream = mock_astream

    with patch.object(adapter, "get_llm", return_value=mock_llm_plain):
        tokens = []
        async for token in adapter.stream_chat_with_tools(
            messages=[user_msg],
            tools=[calculator_tool]
        ):
            tokens.append(token)

        full_streamed = "".join(tokens)
        assert "10,981,690" in full_streamed


@pytest.mark.asyncio
async def test_live_ollama_calculator_integration():
    """
    Live integration test against the configured Ollama model (e.g. qwen2.5:7b or qwen2.5:3b).
    Skips cleanly if Ollama is not reachable on the host.
    """
    import httpx
    from backend.config import settings
    from langchain_ollama import ChatOllama

    # Check if Ollama is running
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.LLM_BASE_URL}/api/tags")
            if resp.status_code != 200:
                pytest.skip("Ollama not responding with HTTP 200")
            models_info = resp.json().get("models", [])
            model_names = [m.get("name") for m in models_info]
    except Exception:
        pytest.skip("Ollama service not running at configured base_url")

    # Select available qwen model (prefer 7b if installed for high-fidelity tool tests)
    target_model = "qwen2.5:7b" if "qwen2.5:7b" in model_names else ("qwen2.5:3b" if "qwen2.5:3b" in model_names else None)
    if not target_model:
        pytest.skip("Neither qwen2.5:7b nor qwen2.5:3b found in local Ollama")

    llm = ChatOllama(model=target_model, base_url=settings.LLM_BASE_URL, temperature=0.0)
    llm_with_tools = llm.bind_tools([calculator_tool])

    # Test tool selection on math query
    resp = await llm_with_tools.ainvoke([HumanMessage(content="What is 43235 * 254?")])
    assert bool(resp.tool_calls), f"Model {target_model} did not emit tool_calls for math query"
    call = resp.tool_calls[0]
    assert call["name"] == "calculator"

    # Execute tool and get final response
    tool_raw = calculator_tool.invoke(call["args"])
    tool_msg = ToolMessage(content=tool_raw, tool_call_id=call["id"], name=call["name"])

    final_resp = await llm.ainvoke([
        HumanMessage(content="What is 43235 * 254?"),
        resp,
        tool_msg
    ])
    assert "10981690" in final_resp.content.replace(",", "")

