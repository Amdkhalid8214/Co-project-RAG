import urllib.request
import urllib.parse
import json
import re
import html
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

def clean_snippet(text: str) -> str:
    """Cleans HTML tags, unescapes entities, and normalizes spaces."""
    if not text:
        return ""
    unescaped = html.unescape(text)
    no_tags = re.sub(r"<[^>]+>", "", unescaped)
    return " ".join(no_tags.split()).strip()

# Common stock tickers mapping
POPULAR_TICKERS = {
    "apple": "AAPL",
    "aapl": "AAPL",
    "nvidia": "NVDA",
    "nvda": "NVDA",
    "microsoft": "MSFT",
    "msft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "googl": "GOOGL",
    "amazon": "AMZN",
    "amzn": "AMZN",
    "tesla": "TSLA",
    "tsla": "TSLA",
    "meta": "META",
    "facebook": "META",
    "netflix": "NFLX",
    "nflx": "NFLX",
    "tata": "TTM",
    "reliance": "RELIANCE.NS",
}

class LiveWebSearch:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 DocuChatAI/2.0"
        }

    def get_stock_data(self, query: str) -> Optional[str]:
        """Fetches live stock price if query mentions stocks/tickers."""
        q_lower = query.lower()
        symbol = None

        for name, sym in POPULAR_TICKERS.items():
            if re.search(rf"\b{name}\b", q_lower):
                symbol = sym
                break

        # Check for explicit ticker like $NVDA, AAPL stock
        ticker_match = re.search(r"\$([A-Za-z]{1,5})\b", query)
        if ticker_match:
            symbol = ticker_match.group(1).upper()

        if not symbol and any(w in q_lower for w in ["stock", "share price", "market price", "trading at"]):
            words = re.findall(r"\b[A-Za-z]+\b", query)
            for w in words:
                w_up = w.upper()
                if w_up in ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "META", "GOOGL", "NFLX", "AMD", "INTC", "SPY", "QQQ"]:
                    symbol = w_up
                    break

        if not symbol:
            return None

        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?interval=1d&range=1d"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                meta = data["chart"]["result"][0]["meta"]
                price = meta.get("regularMarketPrice")
                prev_close = meta.get("chartPreviousClose")
                currency = meta.get("currency", "USD")
                change = round(price - prev_close, 2) if price and prev_close else 0.0
                pct = round((change / prev_close) * 100, 2) if prev_close else 0.0
                sign = "+" if change >= 0 else ""
                return f"[LIVE STOCK DATA] {symbol.upper()} is currently trading at {price} {currency} ({sign}{change} / {sign}{pct}% from previous close of {prev_close} {currency})."
        except Exception as e:
            logger.debug(f"Stock fetch error for {symbol}: {e}")
            return None

    def search_duckduckgo(self, query: str, max_results: int = 3) -> List[str]:
        """Searches DuckDuckGo HTML / Lite for current web results snippets."""
        clean_q = re.sub(r"[^\w\s-]", " ", query).strip()
        results = []

        # Try DDG HTML with fast 2.0s timeout
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(clean_q)}"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                raw_html = resp.read().decode("utf-8", errors="ignore")
                snippets = re.findall(r'class="result__snippet[^"]*"[^>]*>(.*?)</a>', raw_html, re.DOTALL)
                for s in snippets[:max_results]:
                    clean = clean_snippet(s)
                    if clean and len(clean) > 20:
                        results.append(clean)
        except Exception:
            pass

        if results:
            return results

        # Try DDG Lite with fast 2.0s timeout
        try:
            url = "https://lite.duckduckgo.com/lite/"
            data = urllib.parse.urlencode({"q": clean_q}).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=self.headers)
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                raw_html = resp.read().decode("utf-8", errors="ignore")
                snippets = re.findall(r'<td class="result-snippet"[^>]*>(.*?)</td>', raw_html, re.DOTALL)
                for s in snippets[:max_results]:
                    clean = clean_snippet(s)
                    if clean and len(clean) > 20:
                        results.append(clean)
        except Exception:
            pass

        return results

    def search_wikipedia(self, query: str, max_results: int = 2) -> List[str]:
        """Fetches concise Wikipedia entries for topics, figures, movies, etc."""
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&utf8=&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": "DocuChatAI/2.0"})
        try:
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = data.get("query", {}).get("search", [])
                snippets = []
                for r in results[:max_results]:
                    title = r.get("title", "")
                    clean = clean_snippet(r.get("snippet", ""))
                    if clean and len(clean) > 15:
                        snippets.append(f"{title}: {clean}")
                return snippets
        except Exception:
            return []

    def search_structured(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Fallback search provider that returns structured records:
        [{'title': ..., 'url': ..., 'snippet': ..., 'engine': ...}]
        with verified, well-formed HTTP/HTTPS URLs.
        """
        structured: List[Dict[str, str]] = []
        seen_urls = set()

        # 1. Wikipedia search (rich encyclopedia definitions with exact canonical URLs)
        try:
            wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&utf8=&format=json"
            req = urllib.request.Request(wiki_url, headers={"User-Agent": "DocuChatAI/2.0"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("query", {}).get("search", []):
                    title = item.get("title", "").strip()
                    snippet = clean_snippet(item.get("snippet", ""))
                    if title:
                        article_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                        norm_url = article_url.rstrip("/")
                        if norm_url not in seen_urls:
                            seen_urls.add(norm_url)
                            structured.append({
                                "title": f"{title} - Wikipedia",
                                "url": article_url,
                                "snippet": snippet or f"Wikipedia article on {title}.",
                                "engine": "wikipedia"
                            })
                    if len(structured) >= 2:
                        break
        except Exception as e:
            logger.debug(f"[FALLBACK SEARCH] Wikipedia error: {e}")

        # 2. DuckDuckGo structured results
        clean_q = re.sub(r"[^\w\s-]", " ", query).strip()
        try:
            ddg_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(clean_q)}"
            req = urllib.request.Request(ddg_url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                raw_html = resp.read().decode("utf-8", errors="ignore")
                
                # Match result blocks: result__title containing <a> and result__snippet
                blocks = re.findall(r'<div[^>]+class="[^"]*result__body[^"]*"[^>]*>(.*?)</div>\s*</div>', raw_html, re.DOTALL)
                for block in blocks:
                    # Extract link and title
                    a_match = re.search(r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, re.DOTALL)
                    if not a_match:
                        continue
                    raw_href = a_match.group(1).strip()
                    raw_title = clean_snippet(a_match.group(2))
                    
                    # Unquote DuckDuckGo redirect uddg parameter
                    target_url = raw_href
                    if "uddg=" in raw_href:
                        parsed = urllib.parse.urlparse(raw_href)
                        qs = urllib.parse.parse_qs(parsed.query)
                        if "uddg" in qs and qs["uddg"]:
                            target_url = qs["uddg"][0]
                    
                    # Check valid http(s) URL
                    if not target_url.startswith(("http://", "https://")):
                        continue

                    norm_url = target_url.rstrip("/")
                    if norm_url in seen_urls:
                        continue
                    seen_urls.add(norm_url)

                    # Extract snippet
                    s_match = re.search(r'class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>', block, re.DOTALL)
                    snippet_text = clean_snippet(s_match.group(1)) if s_match else ""

                    structured.append({
                        "title": raw_title or "Web Search Result",
                        "url": target_url,
                        "snippet": snippet_text or "Information relevant to the query.",
                        "engine": "duckduckgo"
                    })

                    if len(structured) >= max_results:
                        break
        except Exception as e:
            logger.debug(f"[FALLBACK SEARCH] DuckDuckGo error: {e}")

        # 3. If stock query, prepend stock link
        stock_info = self.get_stock_data(query)
        if stock_info:
            structured.insert(0, {
                "title": f"Market Data for {query}",
                "url": "https://finance.yahoo.com",
                "snippet": stock_info,
                "engine": "yahoo_finance"
            })

        return structured[:max_results]

    def get_live_context(self, query: str) -> str:
        """
        Gathers live real-time information for movies, stocks, sports, politics, etc.
        Returns a concise context string to feed to the LLM.
        """
        q_lower = query.lower()
        # Fast bypass for date/time/temporal/clock/greeting questions
        date_keywords = ["today", "date", "year", "month", "what day", "what time", "current time", "clock", "who are you", "what can you do"]
        if any(k in q_lower for k in date_keywords):
            return ""

        context_parts = []

        # 1. Check live stock market data
        stock_info = self.get_stock_data(query)
        if stock_info:
            context_parts.append(stock_info)

        # 2. Check DuckDuckGo web results
        web_snippets = self.search_duckduckgo(query, max_results=3)
        if web_snippets:
            context_parts.append("Web Search Updates:\n" + "\n".join(f"- {s}" for s in web_snippets))

        # 3. If web snippets are scarce, augment with Wikipedia
        if len(web_snippets) < 2:
            wiki_snippets = self.search_wikipedia(query, max_results=2)
            if wiki_snippets:
                context_parts.append("Encyclopedia Context:\n" + "\n".join(f"- {s}" for s in wiki_snippets))

        return "\n\n".join(context_parts)

live_web_search = LiveWebSearch()
