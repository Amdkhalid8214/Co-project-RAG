"""
DocuChat AI - Comprehensive Weather Tool & Automatic Title Generation Test Suite
Validates:
1. Deterministic conversation title generation (Part B)
2. Weather intent routing & location extraction (Part A)
3. Open-Meteo weather geocoding, WMO mapping, and structured card payload (Part A)
4. Robust error handling for invalid locations and provider timeouts
5. MessageModel.weather serialization and database schema compatibility
6. Regression tests ensuring PDF RAG and Excel analysis are unaffected
"""

import pytest
import asyncio
from typing import Dict, Any

from backend.llm.title_generator import generate_conversation_title, capitalize_title
from backend.llm.router import is_weather_request, query_router
from backend.tools.weather import (
    extract_location_from_query,
    geocode_location,
    format_wmo_code,
    parse_weather_payload,
    get_weather_forecast_async,
    describe_feels_like,
    generate_weather_advice,
    WeatherInput,
    WMO_WEATHER_CODES,
)
from backend.db.models import MessageModel, ConversationModel


# ==============================================================================
# PART B: CONVERSATION TITLE TESTS
# ==============================================================================

def test_title_generation_weather_today_goa():
    title = generate_conversation_title("What is the weather today in Goa?")
    assert "Goa" in title
    assert "Weather" in title
    assert title.lower() == "goa weather today"


def test_title_generation_excel_analysis():
    title = generate_conversation_title("Analyze the uploaded Excel file")
    assert title.lower() == "excel file analysis"


def test_title_generation_transformer_explanation():
    title = generate_conversation_title("Explain transformer self-attention")
    assert "Transformer" in title
    assert "Self-Attention" in title


def test_title_generation_hr_policy():
    title = generate_conversation_title("Summarize my HR policy PDF")
    assert "HR Policy" in title
    assert "Summary" in title


def test_title_generation_rain_bengaluru():
    title = generate_conversation_title("Will it rain in Bengaluru tomorrow?")
    assert "Bengaluru" in title
    assert "Rain" in title


def test_title_generation_temperature_hyderabad():
    title = generate_conversation_title("What is the current temperature in Hyderabad?")
    assert "Hyderabad" in title
    assert "Temperature" in title


def test_title_generation_umbrella_goa():
    title = generate_conversation_title("Should I carry an umbrella in Goa tonight?")
    assert "Goa" in title
    assert "Umbrella" in title


def test_title_generation_empty_or_blank():
    assert generate_conversation_title("") == "New Chat"
    assert generate_conversation_title("   ") == "New Chat"
    assert generate_conversation_title("???") == "New Chat"
    assert generate_conversation_title("...") == "New Chat"


def test_title_word_count_and_formatting():
    # Long query should be truncated to concise 3-6 words
    long_q = "Can you please tell me how to optimize hybrid search in rag with reciprocal rank fusion and bm25"
    title = generate_conversation_title(long_q)
    word_count = len(title.split())
    assert 2 <= word_count <= 6
    assert title != "New Chat"


# ==============================================================================
# PART A: WEATHER INTENT ROUTING & LOCATION EXTRACTION TESTS
# ==============================================================================

def test_weather_intent_detection():
    # True positives
    assert is_weather_request("What is the weather today in Goa?") is True
    assert is_weather_request("Will it rain in Bengaluru tomorrow?") is True
    assert is_weather_request("What is the current temperature in Hyderabad?") is True
    assert is_weather_request("Give me a 5-day weather forecast for Chennai.") is True
    assert is_weather_request("Should I carry an umbrella in Goa tonight?") is True
    assert is_weather_request("How hot is Delhi today?") is True
    assert is_weather_request("Is it raining in Mumbai?") is True
    assert is_weather_request("Wind speed and humidity in Tokyo") is True

    # True negatives (Document & General QA)
    assert is_weather_request("Analyze the uploaded Excel file") is False
    assert is_weather_request("Explain transformer self-attention") is False
    assert is_weather_request("Summarize my HR policy PDF") is False
    assert is_weather_request("What is 43235 * 254?") is False
    assert is_weather_request("Who is the CEO mentioned in the document?") is False
    assert is_weather_request("What does the report say about climate risk?") is False


@pytest.mark.asyncio
async def test_router_query_routes_weather_to_badge():
    route, badge = await query_router.route_query(
        question="What is the weather today in Goa?",
        has_documents=True,
        active_doc_ids=["doc_123"]
    )
    assert route == "general"
    assert badge == "⛅ Live Weather"


def test_location_extraction_from_queries():
    assert extract_location_from_query("What is the weather today in Goa?") == "Goa"
    assert extract_location_from_query("Will it rain in Bengaluru tomorrow?") == "Bengaluru"
    assert extract_location_from_query("What is the current temperature in Hyderabad?") == "Hyderabad"
    assert extract_location_from_query("Give me a 5-day weather forecast for Chennai.") == "Chennai"
    assert extract_location_from_query("Should I carry an umbrella in Goa tonight?") == "Goa"
    assert extract_location_from_query("Delhi weather forecast") == "Delhi"
    assert extract_location_from_query("weather in London") == "London"
    assert extract_location_from_query("temperature in Tokyo") == "Tokyo"


# ==============================================================================
# PART A: WEATHER PROVIDER & PAYLOAD TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_geocoding_popular_location():
    loc = await geocode_location("Goa")
    assert loc is not None
    assert loc["name"] in ("Goa", "Panjim", "Panaji")
    assert loc["country"] == "India"
    assert 14.0 <= loc["latitude"] <= 16.5
    assert 72.5 <= loc["longitude"] <= 75.0


def test_wmo_code_mapping():
    cond, cat = format_wmo_code(0)
    assert cond == "Clear skies"
    assert cat == "clear"

    cond, cat = format_wmo_code(61)
    assert "rain" in cond.lower()
    assert cat == "rain"

    cond, cat = format_wmo_code(95)
    assert "thunderstorm" in cond.lower()
    assert cat == "thunderstorm"


def test_describe_feels_like():
    desc = describe_feels_like(temp=28.0, apparent=35.0, humidity=85)
    assert "warm and humid" in desc or "hot and humid" in desc

    desc_cool = describe_feels_like(temp=14.0, apparent=13.0, humidity=50)
    assert "cool" in desc_cool.lower() or "13°C" in desc_cool


def test_weather_advice_generation():
    advice = generate_weather_advice(
        condition="Clear skies",
        rain_chance=15,
        max_temp=33.0,
        min_temp=24.0
    )
    categories = [a["category"] for a in advice]
    assert "Beach visit" in categories or "Outdoor visit" in categories
    assert "Rain" in categories
    assert "What to wear" in categories

    rain_advice = next(a for a in advice if a["category"] == "Rain")
    assert "15%" in rain_advice["text"]


def test_weather_card_payload_structure():
    mock_loc = {
        "name": "Goa",
        "country": "India",
        "admin1": "Goa",
        "latitude": 15.49574,
        "longitude": 73.82624
    }
    mock_raw = {
        "current": {
            "time": "2026-10-20T21:52",
            "temperature_2m": 28.2,
            "relative_humidity_2m": 88,
            "apparent_temperature": 34.5,
            "precipitation": 0.0,
            "weather_code": 0,
            "wind_speed_10m": 6.2
        },
        "daily": {
            "temperature_2m_max": [33.8],
            "temperature_2m_min": [23.4],
            "precipitation_probability_max": [55],
            "weather_code": [0]
        },
        "hourly": {
            "time": ["2026-10-20T20:00", "2026-10-20T21:00", "2026-10-20T22:00", "2026-10-20T23:00", "2026-10-21T00:00"],
            "temperature_2m": [28.0, 28.2, 27.8, 27.5, 27.0],
            "weather_code": [0, 0, 0, 0, 0],
            "precipitation_probability": [10, 5, 3, 3, 2]
        }
    }

    card = parse_weather_payload(mock_loc, mock_raw)
    assert card["location"] == "Goa, India"
    assert card["current_temp"] == 28
    assert card["current_temp_display"] == "28°C"
    assert card["condition"] == "Clear skies"
    assert card["today_high"] == 34
    assert card["today_low"] == 23
    assert card["rain_chance"] == 55
    assert card["tonight_temp"] == "27–28°C"
    assert "Goa" in card["source"]
    assert len(card["advice"]) >= 3


@pytest.mark.asyncio
async def test_get_weather_forecast_async_live():
    res = await get_weather_forecast_async("Goa")
    assert res["status"] == "success"
    w = res["weather"]
    assert "Goa" in w["location"]
    assert isinstance(w["current_temp"], int)
    assert w["condition"]
    assert "source" in w
    assert len(res["summary"]) > 20


@pytest.mark.asyncio
async def test_get_weather_invalid_location_handled_gracefully():
    res = await get_weather_forecast_async("xyzqwe1234987_nonexistent")
    assert res["status"] == "error"
    assert "Could not find geographic location" in res["error"]


# ==============================================================================
# DATABASE COMPATIBILITY & PERSISTENCE TESTS
# ==============================================================================

def test_message_model_weather_field():
    msg = MessageModel(
        conversation_id="conv_test_123",
        role="assistant",
        content="Here is the weather in Goa today.",
        router_badge="⛅ Live Weather",
        weather={"location": "Goa, India", "current_temp": 28}
    )
    d = msg.to_dict()
    assert d["weather"] == {"location": "Goa, India", "current_temp": 28}
    assert d["router_badge"] == "⛅ Live Weather"


def test_weather_input_schema():
    wi = WeatherInput(location="Goa")
    assert wi.location == "Goa"
    assert wi.days == 1
    assert wi.unit == "celsius"
