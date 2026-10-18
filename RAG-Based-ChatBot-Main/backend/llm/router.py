import re
import logging
from typing import Tuple, Optional, List
from backend.config import settings

logger = logging.getLogger(__name__)

GREETINGS_PATTERN = re.compile(
    r"^(hi|hello|hey|good\s+(morning|afternoon|evening)|howdy|sup|"
    r"(hello|hi|hey)[\s,]+how\s+are\s+you(\s+doing)?|"
    r"how\s+are\s+you(\s+doing)?|"
    r"who\s+are\s+you|what\s+can\s+you\s+do|help|thanks|thank\s+you|bye|goodbye|"
    r"what\s+is\s+(today'?s?\s+)?(the\s+)?(date|day|time|month|year)|"
    r"what\s+day\s+is\s+(today|it)|what\s+time\s+is\s+it|current\s+(date|time|year|month))[.?!]*$",
    re.IGNORECASE
)

VERBATIM_PATTERNS = [
    r"\bextract\s+(the\s+)?(exact|original|verbatim)\b",
    r"\bgive\s+(the\s+)?(exact|original)\s+(paragraph|text|wording|definition|formula|quote|passage)\b",
    r"\bcopy\s+(the\s+)?(formula|text|passage|paragraph|definition|wording)\s+exactly\b",
    r"\bshow\s+(the\s+)?exact\s+wording\b",
    r"\bextract\s+(a\s+|the\s+)?(numbered\s+)?list\s+without\s+changing\s+it\b",
    r"\b(verbatim|word[- ]for[- ]word)\b",
    r"\bquote\s+(the\s+)?exact\b",
    r"\bexact\s+(wording|definition|text)\s+from\s+(the\s+)?(pdf|document|text)\b",
    r"\bwithout\s+(paraphrasing|changing|modifying)\b",
]
VERBATIM_REGEX = re.compile("|".join(VERBATIM_PATTERNS), re.IGNORECASE)


def is_verbatim_extraction_request(question: str) -> bool:
    """
    Identifies explicit exact-text or verbatim extraction requests.
    Document questions asking for explanations, summaries, or general answers
    remain in grounded QA mode and are NOT classified as verbatim extraction.
    """
    if not question:
        return False
    return bool(VERBATIM_REGEX.search(question.strip()))


def is_standalone_math_request(question: str) -> bool:
    """
    Identifies pure standalone calculation questions (e.g. 'What is 43235 * 254?', '18% of 7500').
    These are answered directly by the automatic calculator tool rather than querying document text.
    """
    if not question:
        return False
    s = question.strip()
    s = re.sub(r'^(what\s+is|calculate|compute|solve|evaluate|how\s+much\s+is)\s+', '', s, flags=re.I).rstrip('?. ')
    if re.search(r'\d+(?:\.\d+)?\s*%\s*(of|\*)\s*\d+', s, flags=re.I):
        return True
    allowed_chars = set('0123456789+-*/%^(). x÷×')
    if s and set(s).issubset(allowed_chars) and any(c.isdigit() for c in s) and any(c in '+-*/%^x÷×' for c in s):
        return True
    return False


class QueryRouter:
    def __init__(self, mode: str = settings.ROUTER_MODE):
        self.mode = mode

    def is_verbatim_request(self, question: str) -> bool:
        return is_verbatim_extraction_request(question)

    def is_math_request(self, question: str) -> bool:
        return is_standalone_math_request(question)

    async def detect_intent(
        self,
        question: str,
        has_documents: bool = True,
        active_doc_ids: Optional[List[str]] = None,
        has_external_context: bool = False
    ) -> Tuple[str, str, str]:
        """
        Determines (route, badge, prompt_type) for the request:
        - prompt_type in {"grounded_qa", "verbatim_extraction", "general_chat", "general_chat_with_context"}
        """
        route, badge = await self.route_query(
            question=question,
            has_documents=has_documents,
            active_doc_ids=active_doc_ids
        )

        if route == "document":
            if is_verbatim_extraction_request(question):
                return "document", "Exact Extraction", "verbatim_extraction"
            return "document", badge, "grounded_qa"

        if is_standalone_math_request(question):
            return "general", "🧮 Calculator", "general_chat"

        if has_external_context:
            return "general", "🌐 Live Web Search", "general_chat_with_context"
        return "general", badge, "general_chat"

    async def route_query(
        self,
        question: str,
        has_documents: bool = True,
        active_doc_ids: Optional[List[str]] = None
    ) -> Tuple[str, str]:
        """
        Decides between 'document' question vs 'general' question.
        - When no documents are loaded/scoped: Always 'general' (ChatGPT real-world mode).
        - When documents ARE loaded/scoped:
            - Pure greetings -> 'general'
            - Standalone mathematical calculations -> 'general' (answered via automatic calculator tool)
            - All other questions -> 'document' (prioritize document facts, citations, and highlight).
        """
        clean_q = question.strip()

        # Case 1: No documents uploaded or active -> pure ChatGPT mode
        if not has_documents or (active_doc_ids is not None and len(active_doc_ids) == 0):
            if is_standalone_math_request(clean_q):
                return "general", "🧮 Calculator"
            return "general", "General answer"

        # Case 2: Common conversational pleasantries/greetings
        if GREETINGS_PATTERN.match(clean_q):
            return "general", "General answer"

        # Case 3: Standalone math calculation queries
        if is_standalone_math_request(clean_q):
            return "general", "🧮 Calculator"

        # Case 4: Document is active -> Always route to document pipeline to answer from document!
        return "document", "From document"


query_router = QueryRouter()


