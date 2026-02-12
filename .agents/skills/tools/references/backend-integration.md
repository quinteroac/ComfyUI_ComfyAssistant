# Backend Integration Guide

Complete guide for integrating tool calling with the backend streaming API.

## Overview

The backend's role in the tools system:
1. **Declare** available tools to the LLM
2. **Stream** tool calls from LLM to frontend
3. **Receive** tool results from frontend
4. **Continue** conversation with LLM using results

## Architecture

```
User Message
     ↓
Backend receives request
     ↓
Send to LLM with tools=TOOLS
     ↓
LLM decides to use tool
     ↓
Stream tool-call event to frontend
     ↓
Frontend executes tool
     ↓
Result sent in next request
     ↓
LLM continues with result
     ↓
Stream final response
```

## Step 1: Tool Declarations

### Create tools_definitions.py

```python
"""
Tool definitions for the backend.

These definitions must match the frontend tool definitions exactly.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "addNode",
            "description": "Adds a new node to the ComfyUI workflow",
            "parameters": {
                "type": "object",
                "properties": {
                    "nodeType": {
                        "type": "string",
                        "description": "Node type to add (e.g., 'KSampler', 'CheckpointLoaderSimple')"
                    },
                    "position": {
                        "type": "object",
                        "description": "Optional position on the canvas",
                        "properties": {
                            "x": {"type": "number", "description": "X coordinate"},
                            "y": {"type": "number", "description": "Y coordinate"}
                        }
                    }
                },
                "required": ["nodeType"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "removeNode",
            "description": "Removes a node from the workflow by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "nodeId": {
                        "type": "number",
                        "description": "ID of the node to remove"
                    }
                },
                "required": ["nodeId"]
            }
        }
    }
]


def get_tools():
    """Returns list of available tools."""
    return TOOLS


def get_tool_names():
    """Returns list of tool names."""
    return [tool["function"]["name"] for tool in TOOLS]
```

## Step 2: Update Backend Handler

### Basic Integration (OpenAI-compatible provider)

```python
# __init__.py
import os
import json
from aiohttp import web
from openai import AsyncOpenAI
from tools_definitions import TOOLS

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "llama3-70b-8192")

async def chat_api_handler(request: web.Request) -> web.Response:
    """Handle POST /api/chat with function calling support."""
    try:
        body = await request.json() if request.body_exists else {}
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    
    messages = body.get("messages", [])
    openai_messages = _ui_messages_to_openai(messages)
    
    if not OPENAI_API_KEY:
        # Return placeholder if no API key
        return web.Response(text="API key not configured")
    
    # Create OpenAI-compatible provider client
    client = AsyncOpenAI(
        api_key=OPENAI_API_KEY, 
        base_url="https://api.openai.com/v1"
    )
    
    # Call API with tools
    stream = await client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=openai_messages,
        tools=TOOLS,  # ← Enable function calling
        stream=True,
    )
    
    # Stream response
    resp = web.StreamResponse(
        status=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
    await resp.prepare(request)
    
    async for chunk in stream:
        # Handle different chunk types
        delta = chunk.choices[0].delta if chunk.choices else None
        
        if delta:
            # Handle text content
            if hasattr(delta, 'content') and delta.content:
                await resp.write(f"data: {json.dumps({'type': 'text', 'content': delta.content})}\n\n".encode())
            
            # Handle tool calls
            if hasattr(delta, 'tool_calls') and delta.tool_calls:
                for tool_call in delta.tool_calls:
                    await resp.write(f"data: {json.dumps({'type': 'tool_call', 'tool_call': tool_call.model_dump()})}\n\n".encode())
    
    await resp.write(b"data: [DONE]\n\n")
    return resp
```

### With AI SDK Protocol

For proper AI SDK integration, the SSE events must follow the AI SDK Data Stream format:

```python
def _sse_line(data):
    """Format as SSE data line."""
    return f"data: {json.dumps(data)}\n\n"

async def stream_with_tools():
    """Stream with proper AI SDK protocol."""
    message_id = f"msg_{uuid.uuid4().hex}"
    
    # Start message
    yield _sse_line({"type": "start", "messageId": message_id}).encode("utf-8")
    
    async for chunk in stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        
        if not delta:
            continue
        
        # Handle text content
        if hasattr(delta, 'content') and delta.content:
            # Generate text ID if needed
            if not text_id:
                text_id = f"text_{uuid.uuid4().hex[:24]}"
                yield _sse_line({
                    "type": "text-start",
                    "id": text_id
                }).encode("utf-8")
            
            # Stream text delta
            yield _sse_line({
                "type": "text-delta",
                "id": text_id,
                "delta": delta.content
            }).encode("utf-8")
        
        # Handle tool calls
        if hasattr(delta, 'tool_calls') and delta.tool_calls:
            for tool_call in delta.tool_calls:
                if not tool_call.function:
                    continue
                
                tool_call_id = tool_call.id or f"tool_{uuid.uuid4().hex[:24]}"
                
                # Tool call start
                yield _sse_line({
                    "type": "tool-call-start",
                    "id": tool_call_id,
                    "name": tool_call.function.name
                }).encode("utf-8")
                
                # Tool call arguments
                if tool_call.function.arguments:
                    yield _sse_line({
                        "type": "tool-call-delta",
                        "id": tool_call_id,
                        "argsTextDelta": tool_call.function.arguments
                    }).encode("utf-8")
    
    # End text if we streamed any
    if text_id:
        yield _sse_line({
            "type": "text-end",
            "id": text_id
        }).encode("utf-8")
    
    # Finish message
    yield _sse_line({
        "type": "finish",
        "finishReason": "stop"
    }).encode("utf-8")
    
    yield "data: [DONE]\n\n".encode("utf-8")
```

## Step 3: Handle Tool Results

The frontend sends tool results in the next request. The backend must include them in the conversation:

```python
def _ui_messages_to_openai(messages: list) -> list:
    """Convert UI messages to OpenAI format, including tool results."""
    result = []
    
    for msg in messages or []:
        role = msg.get("role", "user")
        
        if role == "system":
            result.append({"role": "system", "content": _extract_content(msg)})
        
        elif role == "user":
            result.append({"role": "user", "content": _extract_content(msg)})
        
        elif role == "assistant":
            # Assistant message may have tool calls
            assistant_msg = {"role": "assistant", "content": _extract_content(msg) or ""}
            
            # Check for tool calls in the message
            if "toolCalls" in msg:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"])
                        }
                    }
                    for tc in msg["toolCalls"]
                ]
            
            result.append(assistant_msg)
        
        elif role == "tool":
            # Tool result message
            result.append({
                "role": "tool",
                "tool_call_id": msg.get("toolCallId"),
                "content": json.dumps(msg.get("result", {}))
            })
    
    return result
```

## Model Support

### OpenAI-compatible provider Models with Function Calling

```python
# Recommended models for function calling
TOOL_ENABLED_MODELS = [
    "llama3-provider-70b-8192-tool-use-preview",  # Best for tools
    "llama3-provider-8b-8192-tool-use-preview",   # Faster, less accurate
]

# Standard models (may work but less optimized)
STANDARD_MODELS = [
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
]
```

### OpenAI Models

```python
# All recent OpenAI models support function calling
OPENAI_MODELS = [
    "gpt-4-turbo-preview",
    "gpt-4",
    "gpt-3.5-turbo",
]
```

### Check Model Support

```python
async def check_function_calling_support(model: str) -> bool:
    """Check if model supports function calling."""
    tool_models = [
        "tool-use",  # OpenAI-compatible provider tool models
        "gpt-4",     # OpenAI models
        "gpt-3.5",
    ]
    return any(m in model for m in tool_models)
```

## Error Handling

### Handle Tool Call Errors

```python
try:
    stream = await client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=openai_messages,
        tools=TOOLS,
        stream=True,
    )
except Exception as e:
    # Log error
    print(f"Error creating stream: {e}")
    
    # Return error to frontend
    yield _sse_line({
        "type": "error",
        "errorText": str(e)
    }).encode("utf-8")
    return
```

### Handle Streaming Errors

```python
async for chunk in stream:
    try:
        delta = chunk.choices[0].delta if chunk.choices else None
        # Process delta...
    except Exception as e:
        print(f"Error processing chunk: {e}")
        yield _sse_line({
            "type": "error",
            "errorText": f"Stream error: {str(e)}"
        }).encode("utf-8")
        break
```

## Testing

### Test Tool Declaration

```python
# Test that tools are valid JSON
import json

def test_tools_valid():
    try:
        json.dumps(TOOLS)
        print("✅ Tools are valid JSON")
    except Exception as e:
        print(f"❌ Invalid tools: {e}")

test_tools_valid()
```

### Test API Call

```python
# Test function calling with OpenAI-compatible provider
async def test_function_calling():
    client = AsyncOpenAI(
        api_key=OPENAI_API_KEY,
        base_url="https://api.openai.com/v1"
    )
    
    response = await client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "user", "content": "Add a KSampler node"}
        ],
        tools=TOOLS,
        stream=False,  # Non-streaming for testing
    )
    
    # Check if tool was called
    if response.choices[0].message.tool_calls:
        print("✅ Tool was called:", response.choices[0].message.tool_calls)
    else:
        print("❌ No tool call")
```

## System Prompts

Add a system message to guide the LLM in using tools:

```python
SYSTEM_PROMPT = """You are a helpful assistant for ComfyUI, a node-based image generation tool.

You have access to the following tools to interact with ComfyUI workflows:
- addNode: Add a new node to the workflow
- removeNode: Remove a node by ID
- connectNodes: Connect two nodes together
- getWorkflowInfo: Get information about the current workflow

When the user asks to modify the workflow, use these tools to make the changes.
Always confirm what you did after using a tool.

Example:
User: "Add a KSampler node"
You: [call addNode tool] "I've added a KSampler node to your workflow at position (100, 100)."
"""

# Add to messages
openai_messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    *_ui_messages_to_openai(messages)
]
```

## Debugging

### Log Tool Calls

```python
async for chunk in stream:
    delta = chunk.choices[0].delta if chunk.choices else None
    
    if hasattr(delta, 'tool_calls') and delta.tool_calls:
        for tool_call in delta.tool_calls:
            print(f"🔧 Tool called: {tool_call.function.name}")
            print(f"   Arguments: {tool_call.function.arguments}")
```

### Log Full Messages

```python
print("📤 Sending to LLM:")
for msg in openai_messages:
    print(f"  {msg['role']}: {msg.get('content', '[tool call]')}")
```

## Performance Optimization

### Cache Tool Definitions

```python
# Cache at module level (done once)
_CACHED_TOOLS = None

def get_tools():
    global _CACHED_TOOLS
    if _CACHED_TOOLS is None:
        _CACHED_TOOLS = [/* tool definitions */]
    return _CACHED_TOOLS
```

### Reduce Tool Count

Only include tools needed for current context:

```python
def get_relevant_tools(context: str) -> list:
    """Return subset of tools based on context."""
    if "workflow" in context.lower():
        return [t for t in TOOLS if t["function"]["name"] in 
                ["addNode", "removeNode", "connectNodes"]]
    elif "info" in context.lower():
        return [t for t in TOOLS if t["function"]["name"] == "getWorkflowInfo"]
    else:
        return TOOLS
```

## Next Steps

- Review [examples.md](./examples.md) for usage patterns
- Check [architecture.md](./architecture.md) for system design
- See [implementation.md](./implementation.md) for frontend setup
