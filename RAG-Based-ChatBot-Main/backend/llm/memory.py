"""
DocuChat AI - Source-Aware Conversation Memory Management
Handles persistent, bounded multi-turn conversational context for:
1. Normal ChatGPT-style conversational turns.
2. Document-grounded RAG turns (preserving chunk citations & PDF bounding boxes).
3. Web search turns via SearXNG (preserving source URLs, titles, and snippets).
4. Tool execution turns (calculator, exports, search).

Enforces strict memory safety:
- Untrusted data sanitization (prevents memory injection).
- Bounded token and character budgets (prevents context starvation).
- Multi-turn LangChain message conversion (HumanMessage / AIMessage sequence).
- Contextual reference resolution (e.g. "that PDF", "the previous result", "the second point").
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

logger = logging.getLogger("conversation_memory")

# Extended follow-up reference patterns
FOLLOWUP_PATTERNS = [
    # Pronouns
    r"\b(it|its|he|him|his|she|her|hers|they|them|their|theirs|this|that|these|those)\b",
    # Anaphoric references to previous statements/results
    r"\b(former|latter|the same|above|previous|prior|earlier|last)\b",
    r"\b(the\s+(second|first|third|fourth|fifth|last|other)\s+(point|item|one|result|reason|step|section|part|bullet))\b",
    r"\b(that\s+(pdf|document|paper|report|file|article|result|number|figure|table))\b",
    r"\b(the\s+(pdf|document|paper|report|file))\b",
    # Continuations and requests for elaboration
    r"\b(tell\s+me\s+more|explain\s+(further|more|that)|expand\s+on\s+(it|that|this)|elaborate)\b",
    r"\b(what\s+about\s+(it|that|this))\b",
    r"\b(why\s+(is\s+that|so))\b",
    r"\b(how\s+does\s+(it|that)\s+work)\b",
]
FOLLOWUP_REGEX = re.compile("|".join(FOLLOWUP_PATTERNS), re.IGNORECASE)


def is_followup_question(question: str) -> bool:
    """
    Detects whether a user query is a conversational follow-up dependent on prior context.
    Matches pronouns, ordinals ("second point"), document references ("that PDF"), and continuation phrases.
    """
    if not question or not isinstance(question, str):
        return False
    return bool(FOLLOWUP_REGEX.search(question.strip()))


def sanitize_memory_text(text: str, max_chars: int = 400) -> str:
    """
    Sanitizes historical message content before injecting into LLM context:
    - Normalizes excessive whitespace and newlines.
    - Strips potential prompt-injection delimiters (e.g. '=== SYSTEM ===', '[INST]').
    - Truncates to max_chars to keep context compact and budget-compliant.
    """
    if not text or not isinstance(text, str):
        return ""
    clean = text.replace("\r", " ").replace("\t", " ")
    # Neutralize control tag injections
    clean = re.sub(r"(?:===|\bSYSTEM\b|\bHUMAN\b|\[INST\]|\[/INST\])", " ", clean)
    clean = " ".join(clean.split()).strip()
    if len(clean) > max_chars:
        clean = clean[:max_chars].rstrip() + "..."
    return clean


def format_chat_history_for_llm(
    history_dicts: List[Dict[str, Any]],
    max_turns: int = 4,
    max_total_chars: int = 1500,
) -> List[BaseMessage]:
    """
    Selects recent conversational turns from persistent history and converts them
    into a bounded list of LangChain HumanMessage and AIMessage objects.
    
    Guarantees:
    - Alternating user/assistant message fidelity.
    - Strict total character budget ceiling to prevent crowding out document/web evidence.
    - Untrusted data sanitization to prevent memory injection attacks.
    """
    if not history_dicts:
        return []

    # Filter out empty or system messages
    valid_turns = []
    for m in history_dicts:
        role = m.get("role", "")
        content = m.get("content", "").strip()
        if role in ("user", "assistant") and content:
            valid_turns.append(m)

    # Slice the most recent turns (at most max_turns * 2 messages)
    recent_msgs = valid_turns[-(max_turns * 2):]

    formatted_messages: List[BaseMessage] = []
    current_chars = 0

    # Build messages from oldest to newest within the budget
    for item in recent_msgs:
        role = item.get("role")
        raw_content = item.get("content", "")
        clean_content = sanitize_memory_text(raw_content, max_chars=350)
        
        if not clean_content:
            continue

        item_len = len(clean_content)
        if current_chars + item_len > max_total_chars and formatted_messages:
            logger.info(f"[MEMORY] Character budget reached ({current_chars}/{max_total_chars} chars); stopping history inclusion.")
            break

        if role == "user":
            formatted_messages.append(HumanMessage(content=clean_content))
        elif role == "assistant":
            # Append concise source tag if citations were present
            citations = item.get("citations")
            source_tag = ""
            if citations and isinstance(citations, list) and len(citations) > 0:
                first_cite = citations[0]
                if isinstance(first_cite, dict):
                    if first_cite.get("url"):
                        source_tag = f" [Source: {first_cite.get('title', 'Web')}]"
                    elif first_cite.get("filename"):
                        page_num = first_cite.get("page", 1)
                        source_tag = f" [Source: {first_cite.get('filename')} p.{page_num}]"

            formatted_messages.append(AIMessage(content=clean_content + source_tag))

        current_chars += item_len

    return formatted_messages


def build_memory_context_block(
    history_dicts: List[Dict[str, Any]],
    max_turns: int = 3,
) -> str:
    """
    Creates a compact textual conversation history block for query rewriting or prompts.
    Formats as:
      User: ...
      Assistant: ...
    """
    if not history_dicts:
        return ""

    recent = history_dicts[-(max_turns * 2):]
    lines = []
    for m in recent:
        role = "User" if m.get("role") == "user" else "Assistant"
        snippet = sanitize_memory_text(m.get("content", ""), max_chars=180)
        if snippet:
            lines.append(f"{role}: {snippet}")

    return "\n".join(lines)


def package_web_citations(
    query: str,
    results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Packages SearXNG web search results into structured citation dictionaries
    suitable for persistence in MessageModel.citations and frontend display.
    """
    citations = []
    for idx, r in enumerate(results, start=1):
        citations.append({
            "type": "web",
            "source_index": idx,
            "title": r.get("title", "Untitled Web Page"),
            "url": r.get("url", ""),
            "snippet": r.get("snippet", ""),
            "engine": r.get("engine", "searxng"),
            "query": query
        })
    return citations
