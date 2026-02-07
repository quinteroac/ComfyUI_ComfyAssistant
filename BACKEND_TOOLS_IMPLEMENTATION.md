# Backend Tools Implementation

This document describes how tool calling is implemented in the backend (Python) to enable agentic capabilities in ComfyUI Assistant.

## Overview

The backend implements the OpenAI function calling format to:
1. Declare available tools to the LLM (Groq)
2. Stream tool calls from the LLM to the frontend
3. Receive tool execution results from the frontend
4. Continue the conversation with tool results included

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Frontend  │────>│   Backend   │────>│  Groq LLM    │
│  (React)    │     │  (Python)   │     │  (API)       │
└─────────────┘     └─────────────┘     └──────────────┘
      │                    │                     │
      │  1. Chat request   │                     │
      │─────────────────>│                       │
      │                    │  2. Request w/tools │
      │                    │─────────────────────>│
      │                    │                      │
      │                    │  3. Stream tool call │
      │  4. SSE events     │<─────────────────────│
      │<──────────────────│                      │
      │                    │                      │
      │  5. Execute tool   │                      │
      │  (locally)         │                      │
      │                    │                      │
      │  6. Send result    │                      │
      │─────────────────>│                       │
      │                    │  7. Continue w/result│
      │                    │─────────────────────>│
      └────────────────────┴──────────────────────┘
```

## Implementation Details

### 1. System Prompts (`agent_prompts.py`)

Before tools are used, the agent needs instructions on when and how to use them. System prompts define the agent's behavior:

```python
from agent_prompts import get_system_message

# System message is automatically added to every request
openai_messages = _ui_messages_to_openai(messages)

has_system = any(msg.get("role") == "system" for msg in openai_messages)
if not has_system:
    openai_messages.insert(0, get_system_message())
```

**System prompt includes:**
- Agent role and personality
- When to use each tool
- Best practices for tool usage
- Common ComfyUI node types
- Communication guidelines

See `AGENT_PROMPTS_GUIDE.md` for customization details.

### 2. Tool Definitions (`tools_definitions.py`)

Tools are defined in OpenAI function calling format:

```python
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
                        "description": "Node type to add"
                    },
                    # ... more parameters
                },
                "required": ["nodeType"]
            }
        }
    },
    # ... more tools
]
```

### 2. Message Conversion (`_ui_messages_to_openai`)

The backend converts between UI message format and OpenAI format:

**UI Format** (from frontend):
```json
{
  "role": "assistant",
  "parts": [
    {
      "type": "tool-call",
      "toolCallId": "call_abc123",
      "toolName": "addNode",
      "args": {"nodeType": "KSampler"}
    }
  ]
}
```

**OpenAI Format** (to Groq API):
```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "call_abc123",
      "type": "function",
      "function": {
        "name": "addNode",
        "arguments": "{\"nodeType\": \"KSampler\"}"
      }
    }
  ]
}
```

### 3. Streaming Tool Calls

The backend streams tool calls from Groq using Server-Sent Events (SSE):

```python
async def stream_groq():
    tool_call_buffers = {}  # Track streaming tool calls
    
    async for chunk in stream:
        delta = chunk.choices[0].delta
        
        # Handle tool calls
        if hasattr(delta, 'tool_calls') and delta.tool_calls:
            for tool_call in delta.tool_calls:
                tool_call_id = tool_call.id
                
                # Start new tool call
                if tool_call_id not in tool_call_buffers:
                    yield {
                        "type": "tool-call-start",
                        "id": tool_call_id,
                        "name": tool_call.function.name
                    }
                
                # Stream arguments
                if tool_call.function.arguments:
                    yield {
                        "type": "tool-call-delta",
                        "id": tool_call_id,
                        "argsTextDelta": tool_call.function.arguments
                    }
    
    # Close tool calls
    for tool_call_id in tool_call_buffers:
        yield {
            "type": "tool-call-end",
            "id": tool_call_id
        }
```

### 4. SSE Event Types

The backend emits these SSE events for tool calling:

| Event Type | Description | Properties |
|------------|-------------|------------|
| `tool-call-start` | Tool call begins | `id`, `name` |
| `tool-call-delta` | Streaming arguments | `id`, `argsTextDelta` |
| `tool-call-end` | Tool call complete | `id` |

### 5. Tool Result Handling

Tool results come back from the frontend in subsequent requests:

**UI Format** (from frontend):
```json
{
  "role": "tool",
  "parts": [
    {
      "type": "tool-result",
      "toolCallId": "call_abc123",
      "result": {
        "success": true,
        "data": {"nodeId": 42}
      }
    }
  ]
}
```

**OpenAI Format** (to Groq API):
```json
{
  "role": "tool",
  "tool_call_id": "call_abc123",
  "content": "{\"success\": true, \"data\": {\"nodeId\": 42}}"
}
```

## Code Flow

1. **Request arrives**: Frontend sends chat request with message history
2. **Convert messages**: `_ui_messages_to_openai()` converts UI format to OpenAI format
3. **Call Groq**: Backend sends request to Groq with tools defined
4. **Stream response**: 
   - If LLM returns tool calls, stream them to frontend
   - If LLM returns text, stream text normally
5. **Frontend executes**: Frontend receives tool calls and executes them locally
6. **Results return**: Frontend sends tool results in next request
7. **Continue conversation**: Backend includes tool results in conversation history

## Configuration

### Tool Definitions

Tools are automatically loaded in `__init__.py`:

```python
from tools_definitions import TOOLS

# Used in chat API handler
stream = await client.chat.completions.create(
    model=GROQ_MODEL,
    messages=openai_messages,
    tools=TOOLS,  # Tools are passed here
    stream=True,
)
```

### System Prompts

Agent behavior is controlled through system prompts:

```python
from agent_prompts import get_system_message

# System message is injected before each request
openai_messages.insert(0, get_system_message())
```

**Customization options:**

```python
# Standard system message (recommended)
from agent_prompts import get_system_message

# With examples (better performance, more tokens)
from agent_prompts import get_system_message_with_examples

# Minimal (fewer tokens, faster)
from agent_prompts import get_minimal_system_message
```

To customize agent behavior, edit `agent_prompts.py`:
- Modify `SYSTEM_PROMPT` for personality changes
- Update `TOOL_USAGE_GUIDELINES` for tool usage rules
- Extend `NODE_TYPE_REFERENCE` for custom nodes

See `AGENT_PROMPTS_GUIDE.md` for detailed instructions.

## Error Handling

Tool call errors are handled gracefully:

1. **Streaming errors**: Caught and emitted as error SSE events
2. **Execution errors**: Frontend returns error in tool result
3. **Parsing errors**: Invalid tool arguments are rejected by frontend

## Testing

To test tool calling:

1. Start the backend with `GROQ_API_KEY` configured
2. Open the frontend
3. Ask the assistant to perform an action (e.g., "Add a KSampler node")
4. Check browser console for tool execution logs
5. Verify the action was performed in ComfyUI

## Debugging

Enable debug logging to see tool call flow:

```python
# In __init__.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug prints in stream_groq()
print(f"Tool call: {tool_call_id} - {tool_call.function.name}")
print(f"Arguments: {tool_call.function.arguments}")
```

## Related Files

- `__init__.py`: Main backend implementation
- `agent_prompts.py`: System prompts and agent instructions
- `tools_definitions.py`: Tool definitions for Groq
- `ui/src/tools/`: Frontend tool implementations
- `TOOLS_SETUP_GUIDE.md`: Complete setup guide
- `AGENT_PROMPTS_GUIDE.md`: Agent customization guide
- `.agents/skills/tools/`: AI agent documentation

## Next Steps

1. Test tool calling with various scenarios
2. Add more tools as needed
3. Implement error recovery strategies
4. Monitor tool execution performance
