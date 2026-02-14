"""SSE event formatting and AI SDK streaming protocol utilities."""

from __future__ import annotations

import json
import logging
import uuid

logger = logging.getLogger("ComfyUI_ComfyAssistant.sse_streaming")

# AI SDK UI Message Stream headers
UI_MESSAGE_STREAM_HEADERS = {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Vercel-AI-UI-Message-Stream": "v1",
}


def _sse_line(data: dict) -> str:
    """Format a JSON object as an SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


def _stream_ai_sdk_text(text: str, message_id: str):
    """Generate AI SDK Data Stream protocol chunks for a simple text message."""
    text_id = f"msg_{uuid.uuid4().hex[:24]}"
    yield _sse_line({"type": "start", "messageId": message_id})
    yield _sse_line({"type": "text-start", "id": text_id})
    if text:
        yield _sse_line({"type": "text-delta", "id": text_id, "delta": text})
    yield _sse_line({"type": "text-end", "id": text_id})
    yield _sse_line({"type": "finish", "finishReason": "stop"})
    yield "data: [DONE]\n\n"


def _is_tool_ui_part(part: dict) -> bool:
    """Check if a message part is a tool invocation (AI SDK v6 format)."""
    part_type = part.get("type", "")
    return part_type.startswith("tool-") or part_type == "dynamic-tool"


def _get_tool_name(part: dict) -> str:
    """Extract tool name from a tool UI part."""
    part_type = part.get("type", "")
    if part_type == "dynamic-tool":
        return part.get("toolName", "")
    return "-".join(part_type.split("-")[1:])
