"""
Web content extraction with Crawl4AI fallback to aiohttp + BeautifulSoup.

Fetches a URL and returns extracted text content as markdown,
optionally detecting embedded ComfyUI workflows.
"""

import ipaddress
import json
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import aiohttp

logger = logging.getLogger("ComfyUI_ComfyAssistant.web_content")

MAX_CONTENT_LENGTH = 10_000
MAX_DOWNLOAD_SIZE = 5_000_000  # 5 MB


def validate_url(url: str) -> str:
    """Validate and sanitize a URL to prevent SSRF attacks.

    Blocks file://, private IPs, and localhost.

    Args:
        url: URL to validate.

    Returns:
        The validated URL string.

    Raises:
        ValueError: If the URL is invalid or points to a blocked target.
    """
    parsed = urlparse(url)

    # Must have a scheme and netloc
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")

    # Only allow http/https
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Blocked URL scheme: {parsed.scheme}")

    # Extract hostname (strip port if present)
    hostname = parsed.hostname or ""

    # Block localhost
    if hostname in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        raise ValueError("Blocked: localhost URLs are not allowed")

    # Block private/reserved IP ranges
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_reserved or ip.is_loopback or ip.is_link_local:
            raise ValueError(f"Blocked: private/reserved IP address {hostname}")
    except ValueError:
        # hostname is not an IP — that's fine (it's a domain name)
        pass

    return url


def _detect_workflows(text: str) -> List[Dict[str, Any]]:
    """Detect ComfyUI API-format workflows embedded in text.

    Looks for JSON objects that contain nodes with class_type + inputs keys,
    which is the signature of ComfyUI API-format workflows.

    Args:
        text: Text content to scan for workflows.

    Returns:
        List of detected workflow JSON objects.
    """
    workflows: List[Dict[str, Any]] = []

    # Find JSON-like blocks: { ... }
    # Use a simple brace-matching approach for top-level objects
    for match in re.finditer(r'\{', text):
        start = match.start()
        depth = 0
        end = start
        for i in range(start, min(start + 50_000, len(text))):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if depth != 0:
            continue

        candidate = text[start:end]
        if len(candidate) < 20:
            continue

        try:
            obj = json.loads(candidate)
        except (json.JSONDecodeError, RecursionError):
            continue

        if not isinstance(obj, dict):
            continue

        # Check if it looks like a ComfyUI API-format workflow:
        # at least one value should have class_type and inputs
        has_node = False
        for value in obj.values():
            if (
                isinstance(value, dict)
                and "class_type" in value
                and "inputs" in value
            ):
                has_node = True
                break

        if has_node:
            workflows.append(obj)

    return workflows


async def _fetch_crawl4ai(url: str) -> Optional[str]:
    """Attempt to fetch content using Crawl4AI (optional dependency).

    Args:
        url: URL to fetch.

    Returns:
        Markdown content string, or None if Crawl4AI is not available.
    """
    try:
        from crawl4ai import AsyncWebCrawler
    except ImportError:
        return None

    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            if result and result.markdown:
                return result.markdown
    except Exception as e:
        logger.warning("Crawl4AI failed for %s: %s", url, e)

    return None


async def _fetch_aiohttp_bs4(url: str) -> str:
    """Fetch content using aiohttp + BeautifulSoup (lightweight fallback).

    Strips scripts, styles, nav, footer, and header elements.

    Args:
        url: URL to fetch.

    Returns:
        Extracted text content.

    Raises:
        RuntimeError: If the request fails.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError as e:
        raise RuntimeError(
            "beautifulsoup4 package not installed. "
            "Run: pip install beautifulsoup4>=4.12.0"
        ) from e

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ComfyUIAssistant/1.0)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
                max_redirects=5,
            ) as resp:
                resp.raise_for_status()

                # Check content length before downloading
                content_length = resp.headers.get("Content-Length")
                if content_length and int(content_length) > MAX_DOWNLOAD_SIZE:
                    raise RuntimeError(
                        f"Content too large: {content_length} bytes "
                        f"(max {MAX_DOWNLOAD_SIZE})"
                    )

                content_type = resp.headers.get("Content-Type", "")
                if "text/html" not in content_type and "application/xhtml" not in content_type:
                    # For non-HTML, return raw text (truncated)
                    text = await resp.text(errors="replace")
                    return text[:MAX_CONTENT_LENGTH]

                html = await resp.text(errors="replace")
    except aiohttp.ClientError as e:
        raise RuntimeError(f"Failed to fetch {url}: {e}") from e

    # Parse and extract text
    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted elements
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    # Get text with minimal formatting
    text = soup.get_text(separator="\n", strip=True)

    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text


async def fetch_web_content(
    url: str,
    extract_workflow: bool = True,
) -> Dict[str, Any]:
    """Fetch and extract content from a URL.

    Tries Crawl4AI first (if installed), then falls back to
    aiohttp + BeautifulSoup.

    Args:
        url: URL to fetch content from.
        extract_workflow: Whether to scan for embedded ComfyUI workflows.

    Returns:
        Dict with keys: content (str, max 10K chars),
        detectedWorkflows (list), metadata (dict with url, title, provider).

    Raises:
        ValueError: If the URL is invalid or blocked.
        RuntimeError: If content extraction fails.
    """
    url = validate_url(url)

    content: Optional[str] = None
    provider = "unknown"

    # Try Crawl4AI first
    crawl4ai_result = await _fetch_crawl4ai(url)
    if crawl4ai_result is not None:
        content = crawl4ai_result
        provider = "crawl4ai"

    # Fall back to aiohttp + bs4
    if content is None:
        content = await _fetch_aiohttp_bs4(url)
        provider = "aiohttp_bs4"

    # Detect workflows if requested
    detected_workflows: List[Dict[str, Any]] = []
    if extract_workflow and content:
        detected_workflows = _detect_workflows(content)

    # Truncate content
    truncated = len(content) > MAX_CONTENT_LENGTH if content else False
    if content and len(content) > MAX_CONTENT_LENGTH:
        content = content[:MAX_CONTENT_LENGTH]

    return {
        "content": content or "",
        "detectedWorkflows": detected_workflows,
        "metadata": {
            "url": url,
            "provider": provider,
            "truncated": truncated,
            "contentLength": len(content or ""),
        },
    }
