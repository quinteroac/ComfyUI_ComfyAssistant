"""
Tool definitions for the backend.

This file contains the tool definitions in OpenAI Function Calling format
that should be sent to the LLM (Groq) so it knows which tools are available.

IMPORTANT: These definitions must match the tools defined in the frontend
(ui/src/tools/definitions/*)
"""

# Tool definitions in OpenAI Function Calling format
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "addNode",
            "description": "Adds a new node to the ComfyUI workflow. Allows specifying the node type and optionally its position on the canvas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nodeType": {
                        "type": "string",
                        "description": "Node type to add (e.g., 'KSampler', 'CheckpointLoaderSimple', 'LoadImage')"
                    },
                    "position": {
                        "type": "object",
                        "description": "Optional node position on the canvas. If not specified, adds at default position",
                        "properties": {
                            "x": {
                                "type": "number",
                                "description": "X coordinate on the canvas"
                            },
                            "y": {
                                "type": "number",
                                "description": "Y coordinate on the canvas"
                            }
                        },
                        "required": ["x", "y"]
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
            "description": "Removes an existing node from the ComfyUI workflow by its ID.",
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
    },
    {
        "type": "function",
        "function": {
            "name": "connectNodes",
            "description": "Connects two nodes in the ComfyUI workflow. Creates a connection from an output slot of one node to an input slot of another node.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sourceNodeId": {
                        "type": "number",
                        "description": "ID of the source node"
                    },
                    "sourceSlot": {
                        "type": "number",
                        "description": "Output slot index of the source node"
                    },
                    "targetNodeId": {
                        "type": "number",
                        "description": "ID of the target node"
                    },
                    "targetSlot": {
                        "type": "number",
                        "description": "Input slot index of the target node"
                    }
                },
                "required": ["sourceNodeId", "sourceSlot", "targetNodeId", "targetSlot"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "getWorkflowInfo",
            "description": "Gets information about the current ComfyUI workflow, including the list of nodes, connections, and optionally widget names/values for each node.",
            "parameters": {
                "type": "object",
                "properties": {
                    "includeNodeDetails": {
                        "type": "boolean",
                        "description": "If true, includes full details of each node including widget names, types, and current values. Defaults to false for faster responses"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "setNodeWidgetValue",
            "description": "Sets the value of a widget (parameter) on a node. Use getWorkflowInfo with includeNodeDetails first to see available widget names and their current values.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nodeId": {
                        "type": "number",
                        "description": "ID of the node whose widget to set"
                    },
                    "widgetName": {
                        "type": "string",
                        "description": "Name of the widget (e.g., 'steps', 'cfg', 'seed', 'text', 'sampler_name')"
                    },
                    "value": {
                        "description": "New value for the widget (string, number, or boolean)"
                    }
                },
                "required": ["nodeId", "widgetName", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fillPromptNode",
            "description": "Sets the text of a prompt node (CLIPTextEncode). Shorthand for setNodeWidgetValue with widgetName='text'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nodeId": {
                        "type": "number",
                        "description": "ID of the CLIPTextEncode (or similar prompt) node"
                    },
                    "text": {
                        "type": "string",
                        "description": "The prompt text to set"
                    }
                },
                "required": ["nodeId", "text"]
            }
        }
    }
]


def get_tools():
    """
    Returns the list of available tools.
    
    Returns:
        list: List of tool definitions in OpenAI Function Calling format
    """
    return TOOLS


def get_tool_names():
    """
    Returns a list with the names of all available tools.
    
    Returns:
        list: List of tool names
    """
    return [tool["function"]["name"] for tool in TOOLS]


# Usage examples in code:
"""
# In your chat handler (__init__.py):

from tools_definitions import TOOLS

async def chat_api_handler(request: web.Request) -> web.Response:
    # ... existing code ...
    
    stream = await client.chat.completions.create(
        model=GROQ_MODEL,
        messages=openai_messages,
        tools=TOOLS,  # 👈 Add tools here
        stream=True,
    )
    
    async for chunk in stream:
        # Handle tool_calls from stream
        if hasattr(chunk.choices[0].delta, 'tool_calls') and chunk.choices[0].delta.tool_calls:
            tool_calls = chunk.choices[0].delta.tool_calls
            # Process tool_calls and send them as SSE events
            for tool_call in tool_calls:
                # Emit tool-call-start, tool-call-delta, etc.
                pass
"""
