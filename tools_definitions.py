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
    },
    {
        "type": "function",
        "function": {
            "name": "createSkill",
            "description": "Creates a persistent user skill (a remembered instruction or preference). Use when the user says 'remember to...', 'always do...', 'from now on...', etc. The skill will be applied in future conversations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Short, descriptive name for the skill (e.g., 'Use Preview Image', 'Prefer SDXL models')"
                    },
                    "description": {
                        "type": "string",
                        "description": "Brief description of what this skill does"
                    },
                    "instructions": {
                        "type": "string",
                        "description": "Full instructions for the assistant to follow when this skill is active"
                    }
                },
                "required": ["name", "description", "instructions"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "deleteSkill",
            "description": "Deletes a user skill by its slug. Use when the user asks to forget a preference, remove a remembered skill, or delete a specific skill. The slug is the identifier used in the skills list (e.g. 'use-preview-image').",
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": "The slug of the skill to delete (e.g. 'use-preview-image', 'prefer-sdxl-models')"
                    }
                },
                "required": ["slug"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "updateSkill",
            "description": "Updates an existing user skill by slug. Use when the user wants to change the name, description, or instructions of a skill they created earlier. Provide only the fields to change.",
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": "The slug of the skill to update"
                    },
                    "name": {
                        "type": "string",
                        "description": "Optional new human-readable name for the skill"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional new brief description"
                    },
                    "instructions": {
                        "type": "string",
                        "description": "Optional new full instructions (replaces existing)"
                    }
                },
                "required": ["slug"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "refreshEnvironment",
            "description": "Rescans the ComfyUI installation to update the list of installed node types, custom node packages, and available models. Use after installing new custom nodes or models, or when the user asks about their environment.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "searchInstalledNodes",
            "description": "Searches installed node types in the user's ComfyUI installation. Use to find available nodes by name, category, or package. If no results, try refreshEnvironment first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term to match against node name, category, or package (e.g., 'upscale', 'KSampler', 'impact')"
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by node category (e.g., 'sampling', 'image', 'conditioning')"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results to return (default: 20)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "readDocumentation",
            "description": "Fetches documentation for a node type, custom node package, or topic. Returns node inputs/outputs, README excerpts, and any available documentation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic to look up documentation for (e.g., 'KSampler', 'ControlNet', 'comfyui_impact_pack')"
                    },
                    "source": {
                        "type": "string",
                        "enum": ["installed", "builtin", "any"],
                        "description": "Where to search: 'installed' (custom nodes), 'builtin' (system docs), or 'any' (default: 'any')"
                    }
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "getAvailableModels",
            "description": "Lists the user's installed model filenames by category (checkpoints, loras, vae, embeddings, etc.). Use when the user asks for model recommendations (e.g. 'what do you recommend for hyperrealistic?', 'which checkpoint for anime?') so you can suggest specific models they have.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Optional. Filter by category: 'checkpoints', 'loras', 'vae', 'embeddings', etc. If omitted, returns all categories."
                    }
                }
            }
        }
    },
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
