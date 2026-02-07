# Agent Prompts Guide

This guide explains how to customize the system prompts and instructions for the ComfyUI Assistant agent (the LLM that interacts with users via chat).

## Overview

The agent's behavior is controlled through **system prompts** that are sent with every API call to Groq. These prompts teach the LLM:

- When and how to use each tool
- Best practices for tool usage
- How to communicate with users
- Common ComfyUI node types and workflows

## Files

### `agent_prompts.py`

This file contains all system prompts and instructions:

```python
agent_prompts.py
├── SYSTEM_PROMPT              # Main instructions and personality
├── TOOL_USAGE_GUIDELINES      # When and how to use tools
├── TOOL_EXAMPLES              # Few-shot examples (optional)
├── NODE_TYPE_REFERENCE        # Common node types
└── Helper functions           # get_system_message(), etc.
```

### Integration in `__init__.py`

The system message is automatically injected into every chat request:

```python
from agent_prompts import get_system_message

# In chat_api_handler()
openai_messages = _ui_messages_to_openai(messages)

# Add system message if not present
has_system = any(msg.get("role") == "system" for msg in openai_messages)
if not has_system:
    openai_messages.insert(0, get_system_message())
```

## Customizing Agent Behavior

### 1. Modify Agent Personality

Edit `SYSTEM_PROMPT` in `agent_prompts.py`:

```python
SYSTEM_PROMPT = """You are ComfyUI Assistant, an expert AI assistant...

## Your Role
You help users:
- Build and modify ComfyUI workflows
- [Add your custom goals here]
...
"""
```

### 2. Adjust Tool Usage Guidelines

Edit `TOOL_USAGE_GUIDELINES` to change when tools are used:

```python
TOOL_USAGE_GUIDELINES = """
### Use `addNode` when:
- User explicitly asks to add a node
- [Add your custom conditions]
...
"""
```

### 3. Add Custom Node Types

Extend `NODE_TYPE_REFERENCE` with custom nodes:

```python
NODE_TYPE_REFERENCE = """
### Custom Nodes
- **YourCustomNode**: Description (inputs/outputs)
- **AnotherCustomNode**: Description
...
"""
```

### 4. Switch System Message Variants

Use different message functions based on context:

```python
# Standard (recommended)
from agent_prompts import get_system_message

# With examples (more tokens, better initial performance)
from agent_prompts import get_system_message_with_examples

# Minimal (fewer tokens, faster)
from agent_prompts import get_minimal_system_message
```

## System Prompt Structure

### Core Components

1. **Role Definition**: What the agent is and what it does
2. **Capabilities**: What tools are available
3. **Tool Usage Rules**: When to use each tool
4. **Best Practices**: How to use tools effectively
5. **Communication Style**: How to interact with users
6. **Node Reference**: Common node types and workflows
7. **Examples**: Few-shot learning examples (optional)

### Recommended Structure

```
[Agent Identity & Role]
  ↓
[Available Capabilities/Tools]
  ↓
[When to Use Each Tool]
  ↓
[Best Practices & Guidelines]
  ↓
[Communication Style]
  ↓
[Domain Knowledge (Node Types)]
  ↓
[Examples (Optional)]
```

## Best Practices for Prompts

### 1. Be Specific About Tool Usage

❌ **Bad:**
```
Use addNode to add nodes.
```

✅ **Good:**
```
### Use `addNode` when:
- User explicitly asks to add a node ("add a KSampler", "create a CheckpointLoader")
- User describes wanting functionality that requires a specific node
- Building a workflow step-by-step
```

### 2. Provide Concrete Examples

❌ **Bad:**
```
Help users with their workflows.
```

✅ **Good:**
```
**User:** "Add a KSampler node"
**You:** "I'll add a KSampler node to your workflow."
*[Use addNode tool]*
**You:** "I've added a KSampler node (ID: 5) to your canvas."
```

### 3. Include Error Handling Guidance

```python
### Error Handling
- If getWorkflowInfo returns empty, the workflow is blank
- If addNode fails, the node type might be invalid
- If connectNodes fails, check slot indices and node IDs
```

### 4. Set Communication Expectations

```python
## Communication Style
- Be helpful, clear, and concise
- Use technical terms correctly
- Provide context about ComfyUI concepts when needed
- Always confirm before making destructive changes
```

### 5. Teach Domain Knowledge

```python
## Common Node Types
- **KSampler**: Main sampling node (inputs: MODEL, LATENT, positive, negative)
- **VAEDecode**: Converts latents to images (input: VAE, LATENT)
```

## Testing Prompts

### 1. Test Basic Tool Usage

```
User: "Add a KSampler"
Expected: Agent uses addNode tool with nodeType="KSampler"
```

### 2. Test Information Gathering

```
User: "What's in my workflow?"
Expected: Agent uses getWorkflowInfo first, then summarizes
```

### 3. Test Multi-Step Operations

```
User: "Set up a basic txt2img workflow"
Expected: Agent explains plan, adds multiple nodes step-by-step
```

### 4. Test Error Handling

```
User: "Connect node 999 to node 5"
Expected: Agent checks workflow first, reports that node 999 doesn't exist
```

### 5. Test Edge Cases

```
User: "Delete everything"
Expected: Agent asks for confirmation before destructive operation
```

## Advanced Customization

### Dynamic System Messages

You can modify the system message based on context:

```python
def get_system_message(user_expertise="beginner"):
    """Returns system message tailored to user expertise."""
    base_prompt = SYSTEM_PROMPT
    
    if user_expertise == "beginner":
        base_prompt += "\n\n" + BEGINNER_GUIDANCE
    elif user_expertise == "expert":
        base_prompt += "\n\n" + EXPERT_SHORTCUTS
    
    return {
        "role": "system",
        "content": base_prompt
    }
```

### Contextual Tool Guidelines

Adjust guidelines based on workflow state:

```python
def get_contextual_guidelines(workflow_size):
    """Returns guidelines based on workflow complexity."""
    if workflow_size == 0:
        return "The workflow is empty. Suggest starting with basic nodes."
    elif workflow_size > 20:
        return "The workflow is complex. Be careful with modifications."
    else:
        return TOOL_USAGE_GUIDELINES
```

### Custom Few-Shot Examples

Add domain-specific examples:

```python
CUSTOM_EXAMPLES = """
### Example: Your Custom Use Case

User: "Do something specific"

Good approach:
1. Check X
2. Do Y
3. Confirm Z
"""

# Append to TOOL_EXAMPLES
TOOL_EXAMPLES += "\n\n" + CUSTOM_EXAMPLES
```

## Token Usage Optimization

### Measuring Impact

```python
import tiktoken

def count_tokens(text, model="gpt-3.5-turbo"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

# Check token count
system_msg = get_system_message()
tokens = count_tokens(system_msg["content"])
print(f"System prompt uses {tokens} tokens")
```

### Reducing Token Usage

1. **Use minimal system message** for simple queries:
   ```python
   openai_messages.insert(0, get_minimal_system_message())
   ```

2. **Exclude examples** unless needed:
   ```python
   # Remove TOOL_EXAMPLES from get_system_message()
   ```

3. **Compress node reference**:
   ```python
   # Only include most common nodes
   NODE_TYPE_REFERENCE = """
   KSampler, VAEDecode, CheckpointLoaderSimple, SaveImage
   """
   ```

### Caching Strategy

For production, consider caching system prompts:

```python
_SYSTEM_MESSAGE_CACHE = None

def get_cached_system_message():
    global _SYSTEM_MESSAGE_CACHE
    if _SYSTEM_MESSAGE_CACHE is None:
        _SYSTEM_MESSAGE_CACHE = get_system_message()
    return _SYSTEM_MESSAGE_CACHE
```

## Debugging Prompts

### Enable Logging

Add debug output to see what's sent to the API:

```python
# In __init__.py, after adding system message
import logging
logging.basicConfig(level=logging.DEBUG)

logging.debug("System message:")
logging.debug(openai_messages[0]["content"])
```

### Test Prompt Changes

1. Modify `agent_prompts.py`
2. Restart ComfyUI (to reload Python modules)
3. Test in the chat interface
4. Check browser console and server logs

### Common Issues

**Agent not using tools:**
- Check that system prompt mentions the tools
- Verify tool descriptions are clear
- Add more specific "when to use" guidelines

**Agent using tools incorrectly:**
- Add more examples to TOOL_EXAMPLES
- Clarify tool parameter descriptions
- Add error handling guidance

**Agent too verbose/brief:**
- Adjust communication style section
- Add examples of desired response length
- Modify personality traits

## Version Control

When modifying prompts, document changes:

```python
# agent_prompts.py

# Version: 1.1.0
# Changes:
# - Added guidance for custom nodes
# - Improved error handling instructions
# - Shortened node reference

SYSTEM_PROMPT = """..."""
```

## Related Files

- `agent_prompts.py`: Prompt definitions
- `__init__.py`: Prompt integration
- `tools_definitions.py`: Tool schemas (keep in sync!)
- `BACKEND_TOOLS_IMPLEMENTATION.md`: Technical docs
- `.agents/conventions.md`: Development guidelines

## Next Steps

1. Review the default prompts in `agent_prompts.py`
2. Test the agent with various queries
3. Customize prompts based on your use case
4. Monitor agent behavior and iterate
5. Document your prompt changes

## Resources

- **Prompt Engineering Guide**: https://www.promptingguide.ai/
- **OpenAI Function Calling**: https://platform.openai.com/docs/guides/function-calling
- **Groq Documentation**: https://console.groq.com/docs
- **ComfyUI Nodes**: https://docs.comfy.org/essentials/comfyui_nodes
