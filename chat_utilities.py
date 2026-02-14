"""Chat utility functions for error detection, message parsing, and content extraction."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("ComfyUI_ComfyAssistant.chat_utilities")


def _openai_message_content_to_str(msg: dict[str, Any]) -> str:
    """Extract plain text content from an OpenAI-format message."""
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            str(p.get("text", "")) for p in content if isinstance(p, dict)
        )
    return ""


def _set_openai_message_content(msg: dict[str, Any], text: str) -> None:
    """Set an OpenAI-format message content to a plain string."""
    msg["content"] = text


def _is_context_too_large_error(exc: Exception) -> bool:
    """Return True if the exception signals that the request payload / context is too large."""
    status = getattr(exc, "status_code", None) or (
        getattr(getattr(exc, "response", None), "status_code", None)
    )
    if status == 413:
        return True
    # OpenAI and many compatible providers return 400 for context_length_exceeded
    if status == 400:
        msg = str(exc).lower()
        for pattern in (
            "context length",
            "maximum context",
            "token limit",
            "too many tokens",
            "payload too large",
            "content_length",
            "context_length",
            "max_tokens",
            "input too long",
        ):
            if pattern in msg:
                return True
    return False


def _is_context_too_large_response(status: int, body: str) -> bool:
    """Return True if an HTTP response status+body indicates context too large (Anthropic path)."""
    if status == 413:
        return True
    if status == 400:
        lower = body.lower()
        for pattern in (
            "context length",
            "input too long",
            "too many tokens",
            "token limit",
            "payload too large",
            "max_tokens",
        ):
            if pattern in lower:
                return True
    return False


def _get_last_user_text(messages: list[dict[str, Any]]) -> str:
    """Extract the most recent user text from UI messages."""
    for msg in reversed(messages):
        if msg.get("role") != "user":
            continue
        # Try "content" first (OpenAI format), then "parts" (UI format)
        content = msg.get("content") or msg.get("parts")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text = part.get("text")
                    if text:
                        parts.append(text)
            return "".join(parts)
        return ""
    return ""


def _get_last_openai_user_text(messages: list[dict[str, Any]]) -> str:
    """Extract the most recent user content from OpenAI-format messages."""
    for msg in reversed(messages):
        if msg.get("role") != "user":
            continue
        content = msg.get("content")
        if isinstance(content, str):
            return content
        return ""
    return ""
