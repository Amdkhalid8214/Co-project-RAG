"""
DocuChat AI - Safe Public Web Page Fetcher & SSRF Defense Layer
Fetches public web pages with strict security protections:
- Comprehensive SSRF validation (blocks localhost, RFC 1918 private IPs, cloud metadata 169.254.169.254, link-local, loopback)
- Validates redirect targets before following them
- Enforces strict read & connection timeouts
- Limits response payload sizes (max 500 KB)
- Safe HTML text extraction without script/style/nav noise
"""

import html
import ipaddress
import logging
import re
import socket
import urllib.parse
from html.parser import HTMLParser
from typing import Dict, Any, Tuple, Optional, List
import httpx

logger = logging.getLogger("page_fetcher")

# Ports allowed for public web retrieval
ALLOWED_PORTS = {80, 443, 8080, 8443}

# Cloud metadata addresses to strictly block
CLOUD_METADATA_IPS = {
    "169.254.169.254",  # AWS / GCP / Azure metadata
    "fd00:ec2::254",     # AWS IPv6 metadata
}


class HTMLTextExtractor(HTMLParser):
    """
    Fast, standard-library HTML parser that strips scripts, styles, navigation,
    and non-substantive page elements while extracting readable body text.
    """
    IGNORED_TAGS = {
        "script", "style", "noscript", "svg", "header", "footer",
        "nav", "aside", "form", "button", "iframe", "embed", "object"
    }

    def __init__(self):
        super().__init__()
        self.text_chunks: List[str] = []
        self.ignore_depth = 0
        self.in_title = False
        self.page_title = ""

    def handle_starttag(self, tag: str, attrs: list):
        tag_lower = tag.lower()
        if tag_lower == "title":
            self.in_title = True
        if tag_lower in self.IGNORED_TAGS:
            self.ignore_depth += 1
        elif tag_lower in ("p", "div", "br", "h1", "h2", "h3", "h4", "li", "tr", "section", "article"):
            self.text_chunks.append("\n")

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if tag_lower == "title":
            self.in_title = False
        if tag_lower in self.IGNORED_TAGS:
            self.ignore_depth = max(0, self.ignore_depth - 1)
        elif tag_lower in ("p", "div", "h1", "h2", "h3", "h4", "li", "tr", "section", "article"):
            self.text_chunks.append("\n")

    def handle_data(self, data: str):
        if self.in_title and not self.page_title:
            self.page_title = data.strip()
        if self.ignore_depth == 0:
            cleaned = data.strip()
            if cleaned:
                self.text_chunks.append(data)

    def get_text(self, max_chars: int = 3000) -> str:
        raw = "".join(self.text_chunks)
        # Unescape entities
        unescaped = html.unescape(raw)
        # Collapse multiple empty lines
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in unescaped.split("\n")]
        filtered = [l for l in lines if l]
        full_text = "\n".join(filtered)
        if len(full_text) > max_chars:
            # Cut at last space before max_chars
            cut = full_text[:max_chars]
            last_space = cut.rfind(" ")
            if last_space > max_chars - 200:
                cut = cut[:last_space]
            full_text = cut.rstrip() + "..."
        return full_text


def is_safe_public_url(url: str) -> Tuple[bool, str]:
    """
    Validates that a URL is a legitimate, publicly routable HTTP or HTTPS address.
    Strictly protects against Server-Side Request Forgery (SSRF):
    - Scheme must be http or https
    - Hostname cannot be empty or resolve to private, loopback, link-local, or cloud metadata IPs
    - Rejects localhost, internal domains, and IPv6 unique-local addresses
    """
    if not url or not isinstance(url, str):
        return False, "URL is empty or invalid type"

    try:
        parsed = urllib.parse.urlparse(url.strip())
    except Exception as e:
        return False, f"Failed to parse URL: {e}"

    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        return False, f"Unsupported URL scheme: '{scheme}'. Only HTTP and HTTPS are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "URL contains no hostname"

    hostname_lower = hostname.lower()

    # Reject localhost & internal domain suffixes
    if hostname_lower in ("localhost", "127.0.0.1", "::1"):
        return False, "SSRF blocked: Access to localhost is forbidden"

    if hostname_lower.endswith((".local", ".internal", ".lan", ".home", ".corp", ".localdomain")):
        return False, f"SSRF blocked: Internal domain '{hostname}' is forbidden"

    # Reject known cloud metadata hostnames
    if "metadata" in hostname_lower or "169.254" in hostname_lower:
        return False, "SSRF blocked: Cloud metadata endpoint access forbidden"

    # Port validation
    port = parsed.port or (443 if scheme == "https" else 80)
    if port not in ALLOWED_PORTS:
        return False, f"Port {port} is not allowed for web retrieval"

    # DNS Resolution & IP Check
    try:
        # Resolve all IPs for hostname
        addr_info = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
        if not addr_info:
            return False, f"Could not resolve host '{hostname}'"

        for entry in addr_info:
            sockaddr = entry[4]
            ip_str = sockaddr[0]

            if ip_str in CLOUD_METADATA_IPS:
                return False, f"SSRF blocked: Cloud metadata address {ip_str} is forbidden"

            try:
                ip_obj = ipaddress.ip_address(ip_str)
            except ValueError:
                return False, f"Invalid IP address resolved: {ip_str}"

            if ip_obj.is_private:
                return False, f"SSRF blocked: Private network IP {ip_str} is forbidden"
            if ip_obj.is_loopback:
                return False, f"SSRF blocked: Loopback IP {ip_str} is forbidden"
            if ip_obj.is_link_local:
                return False, f"SSRF blocked: Link-local IP {ip_str} is forbidden"
            if ip_obj.is_reserved:
                return False, f"SSRF blocked: Reserved IP {ip_str} is forbidden"
            if ip_obj.is_multicast:
                return False, f"SSRF blocked: Multicast IP {ip_str} is forbidden"

    except socket.gaierror as ge:
        return False, f"DNS resolution failed for '{hostname}': {ge}"
    except Exception as ex:
        return False, f"Security check error for '{hostname}': {ex}"

    return True, "OK"


async def safe_fetch_page_text_async(
    url: str,
    timeout: float = 4.0,
    max_bytes: int = 500_000,
    max_text_chars: int = 3000
) -> Dict[str, Any]:
    """
    Safely retrieves public web page text with SSRF checks, redirect validation,
    byte caps, and clean HTML parsing.
    Returns:
      {
         "url": str,
         "success": bool,
         "text": str,
         "title": str,
         "full_page_read": bool,
         "error": Optional[str]
      }
    """
    is_safe, reason = is_safe_public_url(url)
    if not is_safe:
        logger.warning(f"[PAGE_FETCHER] SSRF check failed for '{url}': {reason}")
        return {
            "url": url,
            "success": False,
            "text": "",
            "title": "",
            "full_page_read": False,
            "error": f"URL blocked: {reason}"
        }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 DocuChatAI/2.0",
        "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
    }

    current_url = url
    max_redirects = 3

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            for _ in range(max_redirects + 1):
                resp = await client.get(current_url, headers=headers)

                # Check for redirects
                if resp.is_redirect:
                    redirect_location = resp.headers.get("Location")
                    if not redirect_location:
                        break
                    # Resolve relative redirect URLs
                    new_url = urllib.parse.urljoin(current_url, redirect_location)
                    # Validate redirect target for SSRF!
                    safe_redirect, redirect_reason = is_safe_public_url(new_url)
                    if not safe_redirect:
                        logger.warning(f"[PAGE_FETCHER] SSRF redirect check failed for '{new_url}': {redirect_reason}")
                        return {
                            "url": url,
                            "success": False,
                            "text": "",
                            "title": "",
                            "full_page_read": False,
                            "error": f"Redirect blocked: {redirect_reason}"
                        }
                    current_url = new_url
                    continue

                # Not a redirect - verify content type
                content_type = resp.headers.get("Content-Type", "").lower()
                if content_type and not any(ct in content_type for ct in ("text/html", "text/plain", "application/xhtml+xml")):
                    return {
                        "url": current_url,
                        "success": False,
                        "text": "",
                        "title": "",
                        "full_page_read": False,
                        "error": f"Unsupported Content-Type '{content_type}'"
                    }

                if resp.status_code != 200:
                    return {
                        "url": current_url,
                        "success": False,
                        "text": "",
                        "title": "",
                        "full_page_read": False,
                        "error": f"HTTP {resp.status_code}"
                    }

                # Read capped bytes
                content_bytes = resp.content[:max_bytes]
                charset = resp.encoding or "utf-8"
                try:
                    raw_html = content_bytes.decode(charset, errors="replace")
                except Exception:
                    raw_html = content_bytes.decode("utf-8", errors="replace")

                # Parse readable text
                parser = HTMLTextExtractor()
                try:
                    parser.feed(raw_html)
                    extracted_text = parser.get_text(max_chars=max_text_chars)
                    page_title = parser.page_title or ""
                except Exception as parse_err:
                    logger.debug(f"[PAGE_FETCHER] HTML parse error: {parse_err}")
                    # Fallback plain regex stripping
                    no_tags = re.sub(r"<[^>]+>", " ", raw_html)
                    extracted_text = " ".join(html.unescape(no_tags).split())[:max_text_chars]
                    page_title = ""

                if not extracted_text or len(extracted_text) < 50:
                    return {
                        "url": current_url,
                        "success": False,
                        "text": "",
                        "title": page_title,
                        "full_page_read": False,
                        "error": "Insufficient readable text extracted from page"
                    }

                return {
                    "url": current_url,
                    "success": True,
                    "text": extracted_text,
                    "title": page_title,
                    "full_page_read": True,
                    "error": None
                }

            return {
                "url": url,
                "success": False,
                "text": "",
                "title": "",
                "full_page_read": False,
                "error": "Too many redirects"
            }

    except httpx.TimeoutException:
        return {
            "url": url,
            "success": False,
            "text": "",
            "title": "",
            "full_page_read": False,
            "error": "Request timed out"
        }
    except Exception as e:
        return {
            "url": url,
            "success": False,
            "text": "",
            "title": "",
            "full_page_read": False,
            "error": str(e)
        }
