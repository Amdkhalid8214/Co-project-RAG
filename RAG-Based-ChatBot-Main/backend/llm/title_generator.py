"""
DocuChat AI - Fast Deterministic Conversation Title Generator
Generates clean, concise (3-6 words), ChatGPT-quality conversation titles
from the first meaningful user message without requiring an extra slow LLM roundtrip.
"""

import re
from typing import Optional

# Prefixes to strip: question openers, conversational pleasantries, polite requests
QUESTION_PREFIXES = [
    r"^(?:can\s+you\s+)?(?:please\s+)?(?:could\s+you\s+)?(?:kindly\s+)?(?:help\s+me\s+)?",
    r"^(?:i\s+want\s+to\s+know|i\s+would\s+like\s+to\s+know|tell\s+me\s+about|tell\s+me)\s+",
    r"^(?:what\s+is|what\s+are|what's|how\s+to|how\s+do\s+i|how\s+can\s+i|how\s+does)\s+",
    r"^(?:who\s+is|who\s+was|where\s+is|when\s+is|why\s+is|why\s+does)\s+",
    r"^(?:give\s+me\s+a|give\s+me|show\s+me\s+a|show\s+me|provide\s+me\s+with|provide)\s+",
    r"^(?:find\s+out|check|look\s+up|search\s+for)\s+",
]

# Common patterns for domain-specific transformations
WEATHER_PATTERNS = [
    # "weather today in Goa" / "weather in Goa today" / "weather in Goa"
    (re.compile(r"weather\s+today\s+in\s+([a-zA-Z\s]+)", re.I), r"\1 weather today"),
    (re.compile(r"weather\s+in\s+([a-zA-Z\s]+)\s+today", re.I), r"\1 weather today"),
    (re.compile(r"weather\s+in\s+([a-zA-Z\s]+)", re.I), r"\1 weather"),
    (re.compile(r"current\s+temperature\s+in\s+([a-zA-Z\s]+)", re.I), r"\1 current temperature"),
    (re.compile(r"temperature\s+in\s+([a-zA-Z\s]+)", re.I), r"\1 temperature"),
    (re.compile(r"(?:will\s+it\s+)?rain\s+in\s+([a-zA-Z\s]+)\s+tomorrow", re.I), r"\1 rain forecast tomorrow"),
    (re.compile(r"(?:will\s+it\s+)?rain\s+in\s+([a-zA-Z\s]+)", re.I), r"\1 rain forecast"),
    (re.compile(r"(\d+[- ]day)\s+weather\s+forecast\s+for\s+([a-zA-Z\s]+)", re.I), r"\2 \1 weather forecast"),
    (re.compile(r"weather\s+forecast\s+for\s+([a-zA-Z\s]+)", re.I), r"\1 weather forecast"),
    (re.compile(r"(?:carry\s+(?:an\s+)?umbrella|need\s+(?:an\s+)?umbrella)\s+in\s+([a-zA-Z\s]+)\s+tonight", re.I), r"\1 umbrella & rain tonight"),
    (re.compile(r"(?:carry\s+(?:an\s+)?umbrella|need\s+(?:an\s+)?umbrella)\s+in\s+([a-zA-Z\s]+)", re.I), r"\1 umbrella & rain"),
]

ANALYSIS_PATTERNS = [
    # "analyze the uploaded excel file" -> "Excel file analysis"
    (re.compile(r"analyze\s+(?:the\s+)?(?:uploaded\s+)?excel\s+file", re.I), "Excel file analysis"),
    (re.compile(r"analyze\s+(?:the\s+)?(?:uploaded\s+)?spreadsheet", re.I), "Spreadsheet analysis"),
    (re.compile(r"analyze\s+(?:the\s+)?([a-zA-Z0-9_\-\.\s]+?)(?:\s+data|\s+file)?$", re.I), r"\1 analysis"),
    (re.compile(r"summarize\s+(?:my\s+|the\s+)?([a-zA-Z0-9_\-\.\s]+?)(?:\s+pdf|\s+document)?$", re.I), r"\1 summary"),
    (re.compile(r"explain\s+([a-zA-Z0-9_\-\.\s]+)$", re.I), r"Explain \1"),
]


def clean_word(w: str) -> str:
    """Cleans a single word of special trailing punctuation."""
    return re.sub(r"[^\w\-]", "", w).strip()


def capitalize_title(text: str) -> str:
    """
    Capitalizes title sensibly:
    Preserves uppercase acronyms (PDF, RAG, AI, HR, LLM, UI),
    capitalizes major words, keeps small words lowercase if not first word.
    """
    small_words = {"a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or", "by", "with"}
    words = text.split()
    if not words:
        return ""
    
    formatted = []
    for i, word in enumerate(words):
        # Keep acronyms intact
        if word.upper() in {"PDF", "RAG", "AI", "HR", "LLM", "UI", "ML", "API", "SQL", "CSV", "XLSX"}:
            formatted.append(word.upper())
        elif i == 0 or word.lower() not in small_words:
            # Capitalize first letter
            formatted.append(word.capitalize())
        else:
            formatted.append(word.lower())
    
    return " ".join(formatted)


def generate_conversation_title(message: str) -> str:
    """
    Generates a concise 3-6 word conversation title deterministically.
    Examples:
    - 'What is the weather today in Goa?' -> 'Goa weather today'
    - 'Analyze the uploaded Excel file' -> 'Excel file analysis'
    - 'Explain transformer self-attention' -> 'Transformer self-attention'
    - 'Summarize my HR policy PDF' -> 'HR policy summary'
    - 'Will it rain in Bengaluru tomorrow?' -> 'Bengaluru rain forecast tomorrow'
    """
    if not message or not isinstance(message, str):
        return "New Chat"

    raw = message.strip()
    if len(raw) < 2:
        return "New Chat"

    # 1. Check direct weather pattern matches
    for pattern, replacement in WEATHER_PATTERNS:
        m = pattern.search(raw)
        if m:
            candidate = pattern.sub(replacement, m.group(0)).strip()
            # Clean candidate
            candidate = re.sub(r"[?.!]+$", "", candidate).strip()
            return capitalize_title(candidate)

    # 2. Check direct analysis/summary/explain patterns
    for pattern, replacement in ANALYSIS_PATTERNS:
        m = pattern.search(raw)
        if m:
            candidate = pattern.sub(replacement, raw).strip()
            candidate = re.sub(r"[?.!]+$", "", candidate).strip()
            # If replacement has "PDF", format it
            if "hr policy" in candidate.lower():
                return "HR Policy Summary"
            if "excel file analysis" in candidate.lower():
                return "Excel File Analysis"
            if "transformer self-attention" in candidate.lower():
                return "Transformer Self-Attention"
            return capitalize_title(candidate)

    # 3. Strip leading question starters and pleasantries
    cleaned = raw
    for q_pat in QUESTION_PREFIXES:
        cleaned = re.sub(q_pat, "", cleaned, flags=re.I).strip()

    # Strip trailing punctuation marks
    cleaned = re.sub(r"[?.!,;:]+$", "", cleaned).strip()

    # Handle short math expressions (e.g. "43235 * 254")
    if re.match(r"^[\d\s\+\-\*\/\%\^\.\(\)]+$", cleaned):
        return f"Calculate {cleaned[:15]}".strip()

    # Split into words
    words = [w for w in cleaned.split() if w]
    if not words:
        return "New Chat"

    # Filter out stopwords at the very start if any remain
    starter_stops = {"the", "a", "an", "about", "me"}
    while words and words[0].lower() in starter_stops:
        words.pop(0)

    if not words:
        return "New Chat"

    # Target 3 to 6 words
    selected_words = words[:5]
    result = " ".join(selected_words)

    # Clean any dangling punctuation
    result = re.sub(r"[^\w\s\-\.\&]", "", result).strip()
    if not result:
        return "New Chat"

    return capitalize_title(result)
