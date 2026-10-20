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


WEATHER_REGEX = re.compile(
    r"\b(weather|temperature|forecast|rainfall|umbrella|humidity|wind\s+speed|precipitat|how\s+(?:hot|cold|warm)|is\s+it\s+(?:raining|sunny|cloudy|snowing)|rain\s+in|snow\s+in)\b",
    re.IGNORECASE
)

DOC_EXPLICIT_REGEX = re.compile(
    r"\b(?:in|from|does|what\s+does|is)\s+(?:the|this)\s+(?:document|pdf|file|context|report|sheet)\b|"
    r"\b(?:the|this)\s+(?:document|pdf|file|report|sheet)\s+(?:says?|states?|mentions?|contains?)\b|"
    r"\b(?:in\s+(?:the\s+)?(?:document|pdf|file|context|text|report|sheet)|from\s+(?:the\s+)?(?:document|pdf|file))\b",
    re.IGNORECASE
)

WEB_SEARCH_PATTERNS = [
    r"\b(?:research\s+(?:on\s+)?(?:the\s+)?(?:internet|web)|research\s+online)\b",
    r"\b(?:search\s+(?:the\s+)?(?:web|internet|online)|look\s+up\s+online|browse\s+the\s+web)\b",
    r"\b(?:google|find\s+on\s+(?:the\s+)?(?:internet|web)|web\s+search\s+for)\b",
    r"\b(?:latest\s+news\s+on|current\s+information\s+about|recent\s+updates\s+on)\b",
]
WEB_SEARCH_REGEX = re.compile("|".join(WEB_SEARCH_PATTERNS), re.IGNORECASE)


def is_weather_request(question: str) -> bool:
    """
    Identifies live weather questions (e.g. 'What is the weather today in Goa?',
    'Will it rain in Bengaluru tomorrow?', 'Should I carry an umbrella in Goa tonight?').
    """
    if not question:
        return False
    q = question.strip()
    # If explicitly asking about document content, do not route to weather
    if DOC_EXPLICIT_REGEX.search(q):
        return False
    return bool(WEATHER_REGEX.search(q))


def is_explicit_web_search_request(question: str) -> bool:
    """
    Identifies explicit web research or internet search requests
    (e.g. 'Research on the internet and give me a guide on how to use OKF',
    'Search the web for Qwen 2.5 benchmarks').
    """
    if not question:
        return False
    q = question.strip()
    if DOC_EXPLICIT_REGEX.search(q):
        return False
    return bool(WEB_SEARCH_REGEX.search(q))


EXCEL_ANALYSIS_REGEX = re.compile(
    r"\b(analyz|analysis|how\s+many\s+(?:rows?|columns?|sheets?)|"
    r"what\s+(?:are|is)\s+(?:the\s+)?(?:columns?|headers?|rows?|sheets?|metrics?)|"
    r"summarize\s+(?:the\s+)?(?:uploaded\s+)?(?:excel|spreadsheet|sheet|file)|"
    r"inspect\s+(?:the\s+)?(?:uploaded\s+)?(?:excel|spreadsheet|sheet)|"
    r"read\s+(?:the\s+)?(?:uploaded\s+)?(?:excel|spreadsheet|sheet))\b",
    re.IGNORECASE
)

EXCEL_INFO_REGEX = re.compile(
    r"^(what\s+is\s+(?:an?\s+)?excel|"
    r"explain\s+excel|"
    r"how\s+does\s+excel\s+work|"
    r"find\s+(?:current\s+)?excel\s+documentation|"
    r"excel\s+tutorial|"
    r"history\s+of\s+excel|"
    r"who\s+(?:created|invented|made)\s+excel|"
    r"difference\s+between\s+excel\s+and)\b",
    re.IGNORECASE
)

EXCEL_GEN_PATTERNS = [
    r"\b(?:create|generate|export|build|prepare|make|produce|write)\b.*\b(?:excel|spreadsheet|workbook|\.xlsx)\b",
    r"\b(?:create|generate|build|prepare|make|produce)\b.*\b(?:test\s+data|test\s+cases?|test\s+suite|test\s+scenarios?)\b",
    r"\b(?:convert|turn)\b.*\b(?:into|to)\b.*\b(?:excel|spreadsheet|workbook|\.xlsx)\b",
    r"\b(?:downloadable|exportable)\s+(?:excel|spreadsheet|workbook|sheet|\.xlsx)\b",
    r"\bexcel\s+(?:sheet|workbook|file)\s+(?:for|with|containing|about)\b",
    r"\b(?:create|generate|provide|give\s+me)\s+(?:a|an)?\s*(?:excel\s+)?(?:sheet|spreadsheet|workbook)\b",
    r"\b(?:positive\s+and\s+negative\s+tests?|valid\s+and\s+invalid\s+(?:examples?|data|inputs?))\b",
]
EXCEL_GEN_REGEX = re.compile("|".join(EXCEL_GEN_PATTERNS), re.IGNORECASE)


def is_excel_generation_request(question: str) -> bool:
    """
    Identifies requests to generate, create, build, or export real Excel (.xlsx) workbooks,
    QA test suites, or downloadable spreadsheets.
    Distinguishes generation from spreadsheet analysis and informational questions.
    """
    if not question:
        return False
    q = question.strip()
    if EXCEL_INFO_REGEX.search(q):
        return False
    if EXCEL_ANALYSIS_REGEX.search(q) and not re.search(r"\b(create|generate|export|build|prepare|make|produce|convert)\b", q, re.I):
        return False
    return bool(EXCEL_GEN_REGEX.search(q))


class QueryRouter:
    def __init__(self, mode: str = settings.ROUTER_MODE):
        self.mode = mode

    def is_verbatim_request(self, question: str) -> bool:
        return is_verbatim_extraction_request(question)

    def is_math_request(self, question: str) -> bool:
        return is_standalone_math_request(question)

    def is_weather(self, question: str) -> bool:
        return is_weather_request(question)

    def is_web_search(self, question: str) -> bool:
        return is_explicit_web_search_request(question)

    def is_excel_generation(self, question: str) -> bool:
        return is_excel_generation_request(question)

    async def detect_intent(
        self,
        question: str,
        has_documents: bool = True,
        active_doc_ids: Optional[List[str]] = None,
        has_external_context: bool = False,
        web_mode: bool = False
    ) -> Tuple[str, str, str]:
        """
        Determines (route, badge, prompt_type) for the request:
        - prompt_type in {"grounded_qa", "verbatim_extraction", "general_chat", "general_chat_with_context", "excel_generation"}
        """
        if is_excel_generation_request(question):
            return "excel_generation", "📊 Excel Generator", "excel_generation"

        route, badge = await self.route_query(
            question=question,
            has_documents=has_documents,
            active_doc_ids=active_doc_ids,
            web_mode=web_mode
        )

        if route == "excel_generation":
            return "excel_generation", "📊 Excel Generator", "excel_generation"

        if route == "document":
            if is_verbatim_extraction_request(question):
                return "document", "Exact Extraction", "verbatim_extraction"
            return "document", badge, "grounded_qa"

        if is_weather_request(question):
            return "general", "⛅ Live Weather", "general_chat"

        if is_standalone_math_request(question):
            return "general", "🧮 Calculator", "general_chat"

        if route == "web" or has_external_context:
            return "web", "🌐 Live Web Search", "general_chat_with_context"
        return "general", badge, "general_chat"

    async def route_query(
        self,
        question: str,
        has_documents: bool = True,
        active_doc_ids: Optional[List[str]] = None,
        web_mode: bool = False
    ) -> Tuple[str, str]:
        """
        Decides between 'document' question vs 'general' question vs 'web' research:
        - When weather is detected -> 'general' (answered via live weather tool)
        - When standalone math is detected -> 'general' (answered via calculator tool)
        - When Web Mode is ON (toggle active in UI):
            - If user explicitly refers to document context -> 'document'
            - Otherwise -> 'web' (grounded in live web research)
        - When user explicitly requests web search (e.g. 'search the web', 'research online') -> 'web'
        - When documents are NOT loaded or active -> 'general'
        - When greetings -> 'general'
        - When documents ARE loaded/active:
            - If an active spreadsheet is present AND (query asks for spreadsheet metrics/terms or scope is purely spreadsheet) -> 'document' (📊 Spreadsheet Analysis)
            - All other document questions -> 'document' (From document)
        """
        clean_q = question.strip()

        # 1. Prioritize live weather queries
        if is_weather_request(clean_q):
            return "general", "⛅ Live Weather"

        # 2. Standalone math calculation queries
        if is_standalone_math_request(clean_q):
            return "general", "🧮 Calculator"

        # 3. Excel Workbook Generation queries
        if is_excel_generation_request(clean_q):
            return "excel_generation", "📊 Excel Generator"

        # 4. Web Mode Active toggle from UI
        if web_mode:
            # If the user explicitly asks about the uploaded document, prioritize document QA
            if DOC_EXPLICIT_REGEX.search(clean_q):
                pass
            else:
                return "web", "🌐 Live Web Search"

        # 4. Case: No documents uploaded or active -> pure ChatGPT mode / web search
        if not has_documents or (active_doc_ids is not None and len(active_doc_ids) == 0):
            if is_explicit_web_search_request(clean_q):
                return "web", "🌐 Live Web Search"
            if GREETINGS_PATTERN.match(clean_q):
                return "general", "General answer"
            return "general", "General answer"

        # 6. Case: Common conversational pleasantries/greetings
        if GREETINGS_PATTERN.match(clean_q):
            return "general", "General answer"

        # 7. Case: Document is active
        from backend.tools.excel_analyzer import active_excel_context
        excel_ctx = active_excel_context.get()
        has_spreadsheet = bool(excel_ctx and excel_ctx.get("has_spreadsheet"))
        has_excel_terms = any(
            k in clean_q.lower()
            for k in (
                "excel", "sheet", "row", "column", "table", "sales", "target",
                "department", "highest", "lowest", "total", "average", "mean",
                "sum", "max", "min", "count", "group", "filter", "spreadsheet", "workbook"
            )
        )
        if has_spreadsheet:
            # Route to Spreadsheet Analysis if spreadsheet terms are mentioned
            # or if the active scope is exclusively spreadsheets
            excel_scoped_ids = set(excel_ctx.get("doc_ids", []))
            if has_excel_terms:
                return "document", "📊 Spreadsheet Analysis"
            if active_doc_ids and excel_scoped_ids and set(active_doc_ids).issubset(excel_scoped_ids):
                return "document", "📊 Spreadsheet Analysis"

        return "document", "From document"


query_router = QueryRouter()



