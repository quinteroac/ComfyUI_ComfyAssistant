"""Provider-specific streaming generators for chat responses."""

from __future__ import annotations

import asyncio
import json
import logging
import tempfile
import uuid
import re
from collections.abc import Callable

from aiohttp import ClientSession

from message_transforms import (
    _build_cli_tool_prompt,
    _cli_response_schema,
    _extract_json_from_text,
    _normalize_cli_structured_response,
    _openai_messages_to_anthropic,
    _openai_tools_to_anthropic,
    _stringify_message_content,
)
from context_management import (
    _estimate_tokens,
    _compact_messages_for_retry,
)
from sse_streaming import _sse_line
from tools_definitions import TOOLS

try:
    import temp_file_store
except ImportError:
    temp_file_store = None

TOOLS_DEFINITIONS = TOOLS

def _parse_thinking_tags(text: str) -> tuple[list[str], str]:
    """Parse <think> tags from text and return reasoning parts + cleaned text."""
    reasoning_parts = []
    # Find all <think>...</think> blocks
    think_pattern = r"<think>(.*?)</think>"
    matches = re.finditer(think_pattern, text, re.DOTALL)

    for match in matches:
        thinking_text = match.group(1).strip()
        if thinking_text:
            reasoning_parts.append(thinking_text)

    # Remove all <think> tags from text
    cleaned_text = re.sub(think_pattern, "", text, flags=re.DOTALL).strip()

    return reasoning_parts, cleaned_text


async def _run_cli_command(
    cmd: list[str],
    timeout_seconds: int,
    stdin_input: bytes | None = None,
) -> tuple[int, str, str, bool]:
    """Run a CLI command with timeout, returning rc/stdout/stderr/timed_out.

    If stdin_input is provided, it is passed to the process stdin (avoids ARG_MAX).
    """
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE if stdin_input is not None else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=stdin_input),
            timeout=timeout_seconds,
        )
        out_str = stdout.decode("utf-8", errors="replace")
        err_str = stderr.decode("utf-8", errors="replace")
        rc = process.returncode or 0
        return (rc, out_str, err_str, False)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        return (124, "", f"Timed out after {timeout_seconds}s", True)


async def stream_openai(
    *,
    message_id: str,
    openai_messages: list[dict],
    openai_api_key: str,
    openai_base_url: str,
    openai_model: str,
    llm_request_delay_seconds: float,
    max_context_compact_retries: int,
    request_tokens_est: int,
    logger: logging.Logger,
    is_context_too_large_error: Callable[[Exception], bool],
    count_request_tokens: Callable[[list[dict]], int],
    tools_definitions: list[dict] = TOOLS_DEFINITIONS,
):
    """Call an OpenAI-compatible API and stream response."""
    from openai import AsyncOpenAI

    # Limit retries on 429 so we fail fast and show a clear message instead of long waits.
    client = AsyncOpenAI(
        api_key=openai_api_key,
        base_url=openai_base_url,
        max_retries=2,
    )

    text_id = f"msg_{uuid.uuid4().hex[:24]}"
    reasoning_id = None
    buffer = ""
    reasoning_sent = False
    text_sent = False  # True once we have sent at least one text-delta (so UI shows a message)
    text_start_emitted = False  # True after we emit text-start (only once per message)
    text_end_sent = False  # True after we emit text-end (must be before tool-input-available for client)
    # Buffer for accumulating tool call chunks
    tool_calls_buffer = {}
    # Accumulate assistant response for debug log
    response_text_parts = []
    response_tool_calls = []
    # Capture finish_reason and usage from the LLM streaming response (last chunk)
    llm_finish_reason = None
    usage_prompt_tokens = None
    usage_completion_tokens = None

    yield _sse_line({"type": "start", "messageId": message_id}).encode("utf-8")

    try:
        await asyncio.sleep(llm_request_delay_seconds)

        # Retry with automatic compaction on 413 / context-too-large
        retry_messages = openai_messages
        stream = None
        for _compact_attempt in range(max_context_compact_retries + 1):
            try:
                stream = await client.chat.completions.create(
                    model=openai_model,
                    messages=retry_messages,
                    tools=tools_definitions,
                    tool_choice="auto",
                    stream=True,
                )
                break  # create() succeeded
            except Exception as create_exc:
                if _compact_attempt < max_context_compact_retries and is_context_too_large_error(create_exc):
                    logger.warning(
                        "[ComfyAssistant] context too large (compact attempt %d/%d), "
                        "applying automatic compaction...",
                        _compact_attempt + 1,
                        max_context_compact_retries,
                    )
                    retry_messages = _compact_messages_for_retry(
                        retry_messages, _compact_attempt + 1
                    )
                    new_est = count_request_tokens(retry_messages)
                    logger.info(
                        "[ComfyAssistant] compacted: %d messages, ~%d tokens (was ~%d)",
                        len(retry_messages),
                        new_est,
                        request_tokens_est,
                    )
                    continue
                raise  # non-retryable or final attempt — propagate to outer handler

        async for chunk in stream:
            choice = chunk.choices[0] if chunk.choices else None
            if not choice:
                continue

            # Last chunk may carry finish_reason and usage
            if choice.finish_reason:
                llm_finish_reason = choice.finish_reason
            if getattr(chunk, "usage", None):
                u = chunk.usage
                if getattr(u, "prompt_tokens", None) is not None:
                    usage_prompt_tokens = u.prompt_tokens
                if getattr(u, "completion_tokens", None) is not None:
                    usage_completion_tokens = u.completion_tokens

            delta = choice.delta

            # Handle text content
            if delta.content:
                buffer += delta.content

                # Check if we have complete thinking blocks
                if "<think>" in buffer and "</think>" in buffer:
                    reasoning_parts, cleaned_text = _parse_thinking_tags(buffer)

                    # Send reasoning parts
                    for reasoning_text in reasoning_parts:
                        if not reasoning_sent:
                            reasoning_id = f"reasoning_{uuid.uuid4().hex[:24]}"
                            yield _sse_line({"type": "reasoning-start", "id": reasoning_id}).encode("utf-8")
                            reasoning_sent = True
                        yield _sse_line({"type": "reasoning-delta", "id": reasoning_id, "delta": reasoning_text}).encode("utf-8")

                    if reasoning_sent and reasoning_id:
                        yield _sse_line({"type": "reasoning-end", "id": reasoning_id}).encode("utf-8")
                        reasoning_sent = False

                    # Start text part for cleaned content (only once)
                    if cleaned_text and not text_start_emitted:
                        yield _sse_line({"type": "text-start", "id": text_id}).encode("utf-8")
                        text_start_emitted = True

                    if cleaned_text:
                        yield _sse_line({"type": "text-delta", "id": text_id, "delta": cleaned_text}).encode("utf-8")
                        text_sent = True
                        response_text_parts.append(cleaned_text)

                    buffer = ""
                else:
                    # Stream normally if no complete thinking blocks yet
                    if "<think>" not in buffer:
                        if not text_start_emitted:
                            yield _sse_line({"type": "text-start", "id": text_id}).encode("utf-8")
                            text_start_emitted = True
                        yield _sse_line({"type": "text-delta", "id": text_id, "delta": delta.content}).encode("utf-8")
                        text_sent = True
                        response_text_parts.append(delta.content)
                        buffer = ""

            # Handle tool calls (Data Stream Protocol format)
            if delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    index = tool_call_delta.index

                    # Initialize tool call buffer if needed
                    if index not in tool_calls_buffer:
                        tool_calls_buffer[index] = {
                            "id": "",
                            "name": "",
                            "arguments": "",
                            "completed": False,
                        }
                    tool_call_data = tool_calls_buffer[index]
                    if tool_call_delta.id:
                        tool_call_data["id"] = tool_call_delta.id
                    if tool_call_delta.function:
                        if tool_call_delta.function.name:
                            tool_call_data["name"] = tool_call_delta.function.name
                        if tool_call_delta.function.arguments:
                            tool_call_data["arguments"] += tool_call_delta.function.arguments
                    # Do not emit tool-input-start / tool-input-delta here. Emitting
                    # only tool-input-available at the end avoids duplicate keys in
                    # assistant-ui (Duplicate key toolCallId-... in tapResources),
                    # which can occur when the client processes tool-input-available
                    # before the part from tool-input-start is committed.

        # Process any remaining buffer
        if buffer:
            reasoning_parts, cleaned_text = _parse_thinking_tags(buffer)

            for reasoning_text in reasoning_parts:
                reasoning_id = f"reasoning_{uuid.uuid4().hex[:24]}"
                yield _sse_line({"type": "reasoning-start", "id": reasoning_id}).encode("utf-8")
                yield _sse_line({"type": "reasoning-delta", "id": reasoning_id, "delta": reasoning_text}).encode("utf-8")
                yield _sse_line({"type": "reasoning-end", "id": reasoning_id}).encode("utf-8")

            if cleaned_text:
                if not text_start_emitted:
                    yield _sse_line({"type": "text-start", "id": text_id}).encode("utf-8")
                    text_start_emitted = True
                yield _sse_line({"type": "text-delta", "id": text_id, "delta": cleaned_text}).encode("utf-8")
                text_sent = True
                response_text_parts.append(cleaned_text)

        # Do NOT emit placeholder text when model returns only tool calls.
        # assistant-ui already renders tool-call parts, so the UI won't be empty.

        # Close text part before tool calls so the client can finalize the message and run tools
        if text_sent and text_id and not text_end_sent:
            yield _sse_line({"type": "text-end", "id": text_id}).encode("utf-8")
            text_end_sent = True

        # Emit tool-input-available for all complete tool calls
        for index, tool_call in tool_calls_buffer.items():
            if tool_call["id"] and tool_call["name"] and tool_call["arguments"] and not tool_call["completed"]:
                try:
                    args = json.loads(tool_call["arguments"])
                    response_tool_calls.append({"name": tool_call["name"], "input": args})
                    yield _sse_line({
                        "type": "tool-input-available",
                        "toolCallId": tool_call["id"],
                        "toolName": tool_call["name"],
                        "input": args,
                    }).encode("utf-8")
                    tool_call["completed"] = True
                except json.JSONDecodeError:
                    # JSON not valid yet, skip
                    pass

        # Token count for this request (real usage or estimate)
        out_tokens = usage_completion_tokens
        if out_tokens is None:
            out_tokens = _estimate_tokens("".join(response_text_parts))
        in_tokens = usage_prompt_tokens if usage_prompt_tokens is not None else request_tokens_est
        logger.info(
            "[ComfyAssistant] tokens in=%s out=%s provider=openai",
            in_tokens,
            out_tokens,
        )

    except Exception as e:
        logger.debug("LLM request failed: %s", e, exc_info=True)
        status = getattr(e, "status_code", None) or (
            getattr(getattr(e, "response", None), "status_code", None)
        )
        if status == 429:
            yield _sse_line({
                "type": "error",
                "errorText": "Rate limit exceeded (429). Please wait a minute and try again.",
            }).encode("utf-8")
        elif is_context_too_large_error(e):
            yield _sse_line({
                "type": "error",
                "errorText": (
                    "Context too large for the model even after automatic compaction. "
                    "Try starting a new conversation or reducing history."
                ),
            }).encode("utf-8")
        else:
            yield _sse_line({"type": "error", "errorText": str(e)}).encode("utf-8")

    if text_sent and text_id and not text_end_sent:
        yield _sse_line({"type": "text-end", "id": text_id}).encode("utf-8")
    # Map OpenAI finish_reason to AI SDK format (underscore → hyphen)
    finish_reason_map = {
        "stop": "stop",
        "tool_calls": "tool-calls",
        "length": "length",
        "content_filter": "content-filter",
    }
    ai_finish = finish_reason_map.get(llm_finish_reason or "stop", "stop")
    yield _sse_line({"type": "finish", "finishReason": ai_finish}).encode("utf-8")
    yield "data: [DONE]\n\n".encode("utf-8")


async def stream_anthropic(
    *,
    message_id: str,
    openai_messages: list[dict],
    anthropic_api_key: str,
    anthropic_model: str,
    anthropic_max_tokens: int,
    anthropic_base_url: str,
    llm_request_delay_seconds: float,
    max_context_compact_retries: int,
    request_tokens_est: int,
    logger: logging.Logger,
    is_context_too_large_response: Callable[[int, str], bool],
    count_request_tokens: Callable[[list[dict]], int],
    tools_definitions: list[dict] = TOOLS_DEFINITIONS,
):
    """Call Anthropic Messages API and stream response."""
    text_id = f"msg_{uuid.uuid4().hex[:24]}"
    text_sent = False
    text_start_emitted = False
    text_end_sent = False
    response_text_parts = []
    response_tool_calls = []
    pending_tool_calls = []
    ai_finish = "stop"

    yield _sse_line({"type": "start", "messageId": message_id}).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    headers["x-api-key"] = anthropic_api_key

    try:
        await asyncio.sleep(llm_request_delay_seconds)

        # Retry with automatic compaction on 413 / context-too-large
        retry_messages = openai_messages
        api_data = None  # parsed JSON response on success
        for _compact_attempt in range(max_context_compact_retries + 1):
            system_text, anthropic_messages = _openai_messages_to_anthropic(
                retry_messages
            )
            payload = {
                "model": anthropic_model,
                "max_tokens": anthropic_max_tokens,
                "messages": anthropic_messages,
                "tools": _openai_tools_to_anthropic(tools_definitions),
                "tool_choice": {"type": "auto"},
            }
            if system_text:
                payload["system"] = system_text

            async with ClientSession() as session:
                async with session.post(
                    f"{anthropic_base_url}/v1/messages",
                    headers=headers,
                    json=payload,
                ) as response:
                    response_text = await response.text()

                    # Check for context-too-large and retry with compaction
                    if is_context_too_large_response(response.status, response_text):
                        if _compact_attempt < max_context_compact_retries:
                            logger.warning(
                                "[ComfyAssistant] context too large (compact attempt %d/%d), "
                                "applying automatic compaction...",
                                _compact_attempt + 1,
                                max_context_compact_retries,
                            )
                            retry_messages = _compact_messages_for_retry(
                                retry_messages, _compact_attempt + 1
                            )
                            new_est = count_request_tokens(retry_messages)
                            logger.info(
                                "[ComfyAssistant] compacted: %d messages, ~%d tokens (was ~%d)",
                                len(retry_messages),
                                new_est,
                                request_tokens_est,
                            )
                            continue
                        # Exhausted retries — show user-friendly error
                        yield _sse_line({
                            "type": "error",
                            "errorText": (
                                "Context too large for the model even after automatic compaction. "
                                "Try starting a new conversation or reducing history."
                            ),
                        }).encode("utf-8")
                        break

                    if response.status >= 400:
                        if response.status == 429:
                            yield _sse_line({
                                "type": "error",
                                "errorText": "Rate limit exceeded (429). Please wait a minute and try again.",
                            }).encode("utf-8")
                        else:
                            error_detail = ""
                            try:
                                error_obj = json.loads(response_text)
                                if isinstance(error_obj, dict):
                                    error = error_obj.get("error", {})
                                    if isinstance(error, dict):
                                        error_detail = error.get("message", "")
                            except json.JSONDecodeError:
                                pass
                            message = error_detail or response_text or "Unknown provider error"
                            yield _sse_line({
                                "type": "error",
                                "errorText": f"Anthropic API error ({response.status}): {message}",
                            }).encode("utf-8")
                        break
                    # Success — process response content
                    api_data = json.loads(response_text)
                    break  # exit retry loop

        # Process successful response (if any)
        if api_data is not None:
            blocks = api_data.get("content", [])
            stop_reason = api_data.get("stop_reason")
            if stop_reason == "tool_use":
                ai_finish = "tool-calls"
            elif stop_reason == "max_tokens":
                ai_finish = "length"

            for block in blocks:
                if not isinstance(block, dict):
                    continue
                block_type = block.get("type")
                if block_type == "text":
                    text = block.get("text", "")
                    if not text:
                        continue
                    if not text_start_emitted:
                        yield _sse_line({
                            "type": "text-start",
                            "id": text_id,
                        }).encode("utf-8")
                        text_start_emitted = True
                    yield _sse_line({
                        "type": "text-delta",
                        "id": text_id,
                        "delta": text,
                    }).encode("utf-8")
                    text_sent = True
                    response_text_parts.append(text)

                if block_type == "tool_use":
                    tool_call_id = block.get("id", "")
                    tool_name = block.get("name", "")
                    tool_input = block.get("input", {})
                    if tool_call_id and tool_name:
                        call_payload = {
                            "name": tool_name,
                            "input": tool_input,
                        }
                        response_tool_calls.append(call_payload)
                        pending_tool_calls.append({
                            "toolCallId": tool_call_id,
                            "toolName": tool_name,
                            "input": tool_input if isinstance(tool_input, dict) else {},
                        })
            usage = api_data.get("usage") or {}
            in_tok = usage.get("input_tokens") or request_tokens_est
            out_tok = usage.get("output_tokens")
            if out_tok is None:
                out_tok = _estimate_tokens("".join(response_text_parts))
            logger.info(
                "[ComfyAssistant] tokens in=%s out=%s provider=anthropic",
                in_tok,
                out_tok,
            )
    except Exception as e:
        logger.debug("Anthropic request failed: %s", e, exc_info=True)
        yield _sse_line({"type": "error", "errorText": str(e)}).encode("utf-8")

    if text_sent and text_id and not text_end_sent:
        yield _sse_line({"type": "text-end", "id": text_id}).encode("utf-8")
        text_end_sent = True
    for tool_call in pending_tool_calls:
        yield _sse_line({
            "type": "tool-input-available",
            "toolCallId": tool_call["toolCallId"],
            "toolName": tool_call["toolName"],
            "input": tool_call["input"],
        }).encode("utf-8")
    yield _sse_line({"type": "finish", "finishReason": ai_finish}).encode("utf-8")
    yield "data: [DONE]\n\n".encode("utf-8")


async def stream_claude_code(
    *,
    message_id: str,
    openai_messages: list[dict],
    claude_code_command: str,
    claude_code_model: str,
    cli_provider_timeout_seconds: int,
    request_tokens_est: int,
    logger: logging.Logger,
):
    """Call Claude Code CLI and stream a normalized response."""
    text_id = f"msg_{uuid.uuid4().hex[:24]}"
    yield _sse_line({"type": "start", "messageId": message_id}).encode("utf-8")

    prompt = _build_cli_tool_prompt(openai_messages)
    schema_json = json.dumps(_cli_response_schema(), ensure_ascii=False)
    prompt_bytes = prompt.encode("utf-8")
    if temp_file_store:
        try:
            temp_file_store.write_temp_file(
                prompt, prefix="prompt", suffix=".txt"
            )
        except Exception:
            pass

    cmd = [claude_code_command, "-p", "-"]
    if claude_code_model:
        cmd.extend(["--model", claude_code_model])
    cmd.extend(["--output-format", "json", "--json-schema", schema_json])

    rc, stdout, stderr, timed_out = await _run_cli_command(
        cmd,
        cli_provider_timeout_seconds,
        stdin_input=prompt_bytes,
    )
    if timed_out:
        yield _sse_line({
            "type": "error",
            "errorText": stderr,
        }).encode("utf-8")
        yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
        yield "data: [DONE]\n\n".encode("utf-8")
        return

    if rc != 0:
        message = stderr.strip() or stdout.strip() or f"{claude_code_command} exited with code {rc}"
        yield _sse_line({"type": "error", "errorText": message}).encode("utf-8")
        yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
        yield "data: [DONE]\n\n".encode("utf-8")
        return

    text, tool_calls = _normalize_cli_structured_response(stdout)
    # Token count: claude_code envelope may include usage
    parsed_env = _extract_json_from_text(stdout)
    in_tok = request_tokens_est
    out_tok = None
    if isinstance(parsed_env, dict):
        usage = parsed_env.get("usage") or {}
        if usage.get("input_tokens") is not None:
            in_tok = usage["input_tokens"]
        if usage.get("output_tokens") is not None:
            out_tok = usage["output_tokens"]
    if out_tok is None:
        out_tok = _estimate_tokens(text)
    logger.info(
        "[ComfyAssistant] tokens in=%s out=%s provider=claude_code",
        in_tok,
        out_tok,
    )
    # Send tool calls; only send text if there are NO tool calls
    # This ensures auto-resubmit works: tool-invocation is the last part
    for tool_call in tool_calls:
        yield _sse_line({
            "type": "tool-input-available",
            "toolCallId": f"call_{uuid.uuid4().hex[:12]}",
            "toolName": tool_call["name"],
            "input": tool_call["input"],
        }).encode("utf-8")
    if text and not tool_calls:
        yield _sse_line({"type": "text-start", "id": text_id}).encode("utf-8")
        yield _sse_line({
            "type": "text-delta",
            "id": text_id,
            "delta": text,
        }).encode("utf-8")
        yield _sse_line({"type": "text-end", "id": text_id}).encode("utf-8")
    finish_reason = "tool-calls" if tool_calls else "stop"
    yield _sse_line({"type": "finish", "finishReason": finish_reason}).encode("utf-8")
    yield "data: [DONE]\n\n".encode("utf-8")


async def stream_codex(
    *,
    message_id: str,
    openai_messages: list[dict],
    codex_command: str,
    codex_model: str,
    cli_provider_timeout_seconds: int,
    request_tokens_est: int,
    logger: logging.Logger,
):
    """Call Codex CLI and stream a normalized response."""
    text_id = f"msg_{uuid.uuid4().hex[:24]}"
    yield _sse_line({"type": "start", "messageId": message_id}).encode("utf-8")

    prompt = _build_cli_tool_prompt(openai_messages)
    prompt_bytes = prompt.encode("utf-8")
    if temp_file_store:
        try:
            temp_file_store.write_temp_file(
                prompt, prefix="prompt", suffix=".txt"
            )
        except Exception:
            pass

    with tempfile.NamedTemporaryFile(prefix="codex-last-", suffix=".txt", delete=True) as tmp, tempfile.NamedTemporaryFile(prefix="codex-schema-", suffix=".json", mode="w", encoding="utf-8", delete=True) as schema_file:
        json.dump(_cli_response_schema(), schema_file, ensure_ascii=False)
        schema_file.flush()
        cmd = [
            codex_command,
            "exec",
            "--skip-git-repo-check",
            "--color",
            "never",
            "--output-schema",
            schema_file.name,
            "-o",
            tmp.name,
            "-",
        ]
        if codex_model:
            cmd.extend(["--model", codex_model])
        rc, stdout, stderr, timed_out = await _run_cli_command(
            cmd,
            cli_provider_timeout_seconds,
            stdin_input=prompt_bytes,
        )
        if timed_out:
            yield _sse_line({
                "type": "error",
                "errorText": stderr,
            }).encode("utf-8")
            yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
            yield "data: [DONE]\n\n".encode("utf-8")
            return

        if rc != 0:
            message = stderr.strip() or stdout.strip() or f"{codex_command} exited with code {rc}"
            yield _sse_line({"type": "error", "errorText": message}).encode("utf-8")
            yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
            yield "data: [DONE]\n\n".encode("utf-8")
            return

        last_message = ""
        try:
            with open(tmp.name, "r", encoding="utf-8") as f:
                last_message = f.read().strip()
        except Exception:
            last_message = ""
        raw = last_message or stdout.strip()
        text, tool_calls = _normalize_cli_structured_response(raw)
        in_tok = request_tokens_est
        out_tok = _estimate_tokens(text)
        logger.info(
            "[ComfyAssistant] tokens in=%s out=%s provider=codex",
            in_tok,
            out_tok,
        )
        # Send tool calls; only send text if there are NO tool calls
        # This ensures auto-resubmit works: tool-invocation is the last part
        for tool_call in tool_calls:
            yield _sse_line({
                "type": "tool-input-available",
                "toolCallId": f"call_{uuid.uuid4().hex[:12]}",
                "toolName": tool_call["name"],
                "input": tool_call["input"],
            }).encode("utf-8")
        if text and not tool_calls:
            yield _sse_line({"type": "text-start", "id": text_id}).encode("utf-8")
            yield _sse_line({
                "type": "text-delta",
                "id": text_id,
                "delta": text,
            }).encode("utf-8")
            yield _sse_line({"type": "text-end", "id": text_id}).encode("utf-8")
        finish_reason = "tool-calls" if tool_calls else "stop"
    yield _sse_line({"type": "finish", "finishReason": finish_reason}).encode("utf-8")
    yield "data: [DONE]\n\n".encode("utf-8")


async def stream_gemini_cli(
    *,
    message_id: str,
    openai_messages: list[dict],
    gemini_cli_command: str,
    gemini_cli_model: str,
    cli_provider_timeout_seconds: int,
    request_tokens_est: int,
    logger: logging.Logger,
):
    """Call Gemini CLI and stream a normalized response."""
    text_id = f"msg_{uuid.uuid4().hex[:24]}"
    yield _sse_line({"type": "start", "messageId": message_id}).encode("utf-8")

    last_msg_role = (openai_messages[-1].get("role") or "") if openai_messages else ""
    last_user_content = ""
    for msg in openai_messages:
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = msg.get("content")
            last_user_content = content if isinstance(content, str) else str(content)
    # Last round of tool results = trailing consecutive "tool" messages
    last_tool_contents = []
    for msg in reversed(openai_messages):
        if not isinstance(msg, dict) or msg.get("role") != "tool":
            break
        content = msg.get("content")
        last_tool_contents.append(content if isinstance(content, str) else str(content))
    last_tool_contents.reverse()
    if last_msg_role == "user" and last_user_content:
        logger.info("[ComfyAssistant] User message: %s", last_user_content[:500] + ("..." if len(last_user_content) > 500 else ""))
    elif last_msg_role == "tool" and last_tool_contents:
        summary = " | ".join((c[:120] + ("..." if len(c) > 120 else "") for c in last_tool_contents[:5]))
        logger.info("[ComfyAssistant] Follow-up after tool call (msgs=%d), tool response(s): %s", len(openai_messages), summary)
    elif len(openai_messages) > 2:
        logger.info("[ComfyAssistant] Follow-up request (msgs=%d)", len(openai_messages))

    prompt = _build_cli_tool_prompt(openai_messages)
    schema_json = json.dumps(_cli_response_schema(), ensure_ascii=False)
    full_prompt = (
        prompt
        + "\n\nIMPORTANT: You MUST respond with a single JSON object matching this schema:\n"
        + schema_json
    )
    full_prompt_bytes = full_prompt.encode("utf-8")
    if temp_file_store:
        try:
            temp_file_store.write_temp_file(
                full_prompt, prefix="prompt", suffix=".txt"
            )
        except Exception:
            pass

    cmd = [gemini_cli_command, "-p", "-", "--output-format", "json"]
    if gemini_cli_model:
        cmd.extend(["-m", gemini_cli_model])

    rc, stdout, stderr, timed_out = await _run_cli_command(
        cmd,
        cli_provider_timeout_seconds,
        stdin_input=full_prompt_bytes,
    )
    if timed_out:
        yield _sse_line({
            "type": "error",
            "errorText": stderr,
        }).encode("utf-8")
        yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
        yield "data: [DONE]\n\n".encode("utf-8")
        return

    if rc != 0:
        message = stderr.strip() or stdout.strip() or f"{gemini_cli_command} exited with code {rc}"
        yield _sse_line({"type": "error", "errorText": message}).encode("utf-8")
        yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
        yield "data: [DONE]\n\n".encode("utf-8")
        return

    # Gemini CLI JSON envelope: {"response": "...", "stats": {...}, "error": {...}}
    # Unwrap the envelope before normalizing.
    raw = stdout.strip()
    in_tok = request_tokens_est
    out_tok = None
    gemini_env = _extract_json_from_text(raw)
    if isinstance(gemini_env, dict) and "response" in gemini_env:
        # Extract token stats from Gemini envelope
        stats = gemini_env.get("stats")
        if isinstance(stats, dict):
            if stats.get("inputTokens") is not None:
                in_tok = stats["inputTokens"]
            elif stats.get("input_tokens") is not None:
                in_tok = stats["input_tokens"]
            if stats.get("outputTokens") is not None:
                out_tok = stats["outputTokens"]
            elif stats.get("output_tokens") is not None:
                out_tok = stats["output_tokens"]
        # Check for Gemini-level error
        gemini_error = gemini_env.get("error")
        if isinstance(gemini_error, dict) and gemini_error.get("message"):
            yield _sse_line({
                "type": "error",
                "errorText": gemini_error["message"],
            }).encode("utf-8")
            yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
            yield "data: [DONE]\n\n".encode("utf-8")
            return
        raw = gemini_env["response"] if isinstance(gemini_env["response"], str) else json.dumps(gemini_env["response"])

    logger.info(
        "[ComfyAssistant] gemini_cli raw response: %s",
        raw[:500] if raw else "(empty)",
    )
    text, tool_calls = _normalize_cli_structured_response(raw)
    logger.info(
        "[ComfyAssistant] gemini_cli parsed: text=%r tool_calls=%d",
        text[:200] if text else "(empty)",
        len(tool_calls),
    )
    if out_tok is None:
        out_tok = _estimate_tokens(text)
    logger.info(
        "[ComfyAssistant] tokens in=%s out=%s provider=gemini_cli",
        in_tok,
        out_tok,
    )
    # Emit text first when present so the user sees the assistant's reply even when tools are also invoked in the same turn.
    # Send multiple text-delta chunks so the frontend accumulates them (validates no overwriting) and shows streaming.
    text_delta_chunk_size = 64
    if text:
        yield _sse_line({"type": "text-start", "id": text_id}).encode("utf-8")
        for i in range(0, len(text), text_delta_chunk_size):
            yield _sse_line({
                "type": "text-delta",
                "id": text_id,
                "delta": text[i : i + text_delta_chunk_size],
            }).encode("utf-8")
        yield _sse_line({"type": "text-end", "id": text_id}).encode("utf-8")
    elif not tool_calls:
        # No text and no tool calls: show fallback so the user sees something
        reply = raw.strip() if raw.strip() else "(No response from model)"
        yield _sse_line({"type": "text-start", "id": text_id}).encode("utf-8")
        for i in range(0, len(reply), text_delta_chunk_size):
            yield _sse_line({
                "type": "text-delta",
                "id": text_id,
                "delta": reply[i : i + text_delta_chunk_size],
            }).encode("utf-8")
        yield _sse_line({"type": "text-end", "id": text_id}).encode("utf-8")

    for tool_call in tool_calls:
        yield _sse_line({
            "type": "tool-input-available",
            "toolCallId": f"call_{uuid.uuid4().hex[:12]}",
            "toolName": tool_call["name"],
            "input": tool_call["input"],
        }).encode("utf-8")
    finish_reason = "tool-calls" if tool_calls else "stop"
    yield _sse_line({"type": "finish", "finishReason": finish_reason}).encode("utf-8")
    yield "data: [DONE]\n\n".encode("utf-8")
