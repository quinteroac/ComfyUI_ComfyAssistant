"""
Tool definitions for the backend.

This file contains the tool definitions in OpenAI Function Calling format
that should be sent to the LLM (OpenAI-compatible provider) so it knows which tools are available.

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
            "description": "Gets information about the current ComfyUI workflow, including the list of nodes, connections, and optionally widget names/values for each node. Returns a compact representation by default (no layout info, no widget option lists).",
            "parameters": {
                "type": "object",
                "properties": {
                    "includeNodeDetails": {
                        "type": "boolean",
                        "description": "If true, includes widget names and current values for each node. Defaults to false for faster responses"
                    },
                    "includeLayout": {
                        "type": "boolean",
                        "description": "If true, includes node position, size, and canvas dimensions. Defaults to false (layout info is rarely needed for reasoning)"
                    },
                    "includeWidgetOptions": {
                        "type": "boolean",
                        "description": "If true, includes available options for combo/dropdown widgets. Defaults to false to reduce payload size (option lists can be very large)"
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
            "name": "getUserSkill",
            "description": "Loads a user skill's full instructions by slug. Use after listUserSkills when the user refers to a saved preference or when you need to apply a remembered skill. Returns slug, name, description, and instructions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": "The slug of the skill to load (e.g. 'use-preview-image', 'prefer-sdxl-models')"
                    }
                },
                "required": ["slug"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "listUserSkills",
            "description": "Lists the user's saved skills (slug, name, description). Use this to see which skills exist before loading one with getUserSkill(slug) when the user refers to a preference or you need to apply a remembered instruction.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "listSystemSkills",
            "description": "Lists model-specific system skills (Flux, SDXL, Lumina2, etc.) available on demand. Returns slug and name. When the user asks about a model or a workflow for a model, call this first to find the matching skill, then getSystemSkill(slug) to load it before answering or building the workflow.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "getSystemSkill",
            "description": "Loads a model-specific system skill by slug (e.g. 09_model_flux, 13_model_sdxl). Call after listSystemSkills when the user asks about a model or a workflow for a model; match the model name to the skill and load it before answering or creating the workflow. Returns slug, name, and full content to apply.",
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": "The slug of the system skill (e.g. '09_model_flux', '13_model_sdxl')"
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
            "description": "Lists the user's installed model filenames by category (checkpoints, loras, vae, unet, diffusion_models, etc.). IMPORTANT: Modern models like Anima, Flux, or Wan are often in 'diffusion_models' or 'unet' folders, not 'checkpoints'. Use this to verify if the user has a specific model or to make recommendations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Optional. Filter by category: 'checkpoints', 'loras', 'vae', 'unet', 'diffusion_models', etc. If omitted, returns all categories."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "executeWorkflow",
            "description": "Queues the current ComfyUI workflow for execution, waits for completion, and returns status and output summary (images, errors). Use when the user says 'run', 'execute', 'generate', or 'queue the workflow'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timeout": {
                        "type": "number",
                        "description": "Maximum time in seconds to wait for execution to complete (default: 300)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "applyWorkflowJson",
            "description": "Loads a complete ComfyUI workflow, replacing the current graph. Accepts two formats: (1) API format: object with string node IDs as keys and values { class_type, inputs, optional _meta.title }. (2) Frontend format: object with nodes (array) and links (array), as exported by ComfyUI or returned by official/custom templates. Use for complex workflows that would take many addNode/connectNodes calls. Prefer applyTemplate when loading from template id; use applyWorkflowJson for raw JSON. Always call searchInstalledNodes and getAvailableModels first when building or validating workflows.",
            "parameters": {
                "type": "object",
                "properties": {
                    "workflow": {
                        "type": "object",
                        "description": "Workflow in either format. API format: keys are string node IDs (e.g. '1', '2'), each value has class_type (string), inputs (object), optional _meta.title. Frontend format: object with nodes (array of node objects with id, type, pos, widgets_values, etc.) and links (array of link tuples). Templates and ComfyUI exports typically use frontend format.",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "class_type": {
                                    "type": "string",
                                    "description": "The registered node type name"
                                },
                                "inputs": {
                                    "type": "object",
                                    "description": "Node inputs: scalar values or links as [nodeId, outputIndex]"
                                },
                                "_meta": {
                                    "type": "object",
                                    "properties": {
                                        "title": {
                                            "type": "string",
                                            "description": "Display title for the node"
                                        }
                                    }
                                }
                            },
                            "required": ["class_type", "inputs"]
                        }
                    }
                },
                "required": ["workflow"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "getExampleWorkflow",
            "description": "Fetches example workflows extracted from the ComfyUI_examples repository. Use this before webSearch when the user asks for a complete workflow for a known model category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": [
                            "flux",
                            "flux2",
                            "lumina2",
                            "qwen_image",
                            "sdxl",
                            "wan",
                            "wan22",
                            "z_image"
                        ],
                        "description": "Example category to search (matches ComfyUI_examples folders)."
                    },
                    "query": {
                        "type": "string",
                        "description": "Optional substring to match example image or JSON filenames."
                    },
                    "maxResults": {
                        "type": "number",
                        "description": "Maximum number of results to return (default: 5, max: 20)."
                    }
                },
                "required": ["category"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "webSearch",
            "description": "Searches the web for ComfyUI-related information, tutorials, workflows, documentation, and custom node guides. Use when the user asks about unfamiliar topics, needs help finding resources, or when your built-in knowledge is insufficient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'ComfyUI ControlNet tutorial', 'SDXL inpainting workflow')"
                    },
                    "maxResults": {
                        "type": "number",
                        "description": "Maximum number of results to return (default: 5, max: 20)"
                    },
                    "timeRange": {
                        "type": "string",
                        "enum": ["day", "week", "month", "year"],
                        "description": "Optional time filter for recency (e.g., 'week' for results from the last week)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetchWebContent",
            "description": "Fetches and extracts content from a URL, returning text (up to 10K chars) and optionally detecting embedded ComfyUI workflows. Use when the user shares a link or when you need to read a specific page found via webSearch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to fetch content from (must be http or https)"
                    },
                    "extractWorkflow": {
                        "type": "boolean",
                        "description": "Whether to scan content for embedded ComfyUI API-format workflows (default: true)"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "searchNodeRegistry",
            "description": "Searches the ComfyUI Registry (comfyregistry.org) for custom node packages. Use when the user needs a node type that is not installed, or wants to discover available custom node packages for a specific purpose.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term (e.g., 'face detection', 'upscale', 'controlnet')"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum results per page (default: 10, max: 50)"
                    },
                    "page": {
                        "type": "number",
                        "description": "Page number for pagination (default: 1)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "searchTemplates",
            "description": "Searches for official and community workflow templates by title, description, or category (e.g., 'wan', 'flux', 'anima', 'i2v'). ALWAYS call this tool first before webSearch when the user asks for a workflow for a specific model or task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Term to search for in template titles or descriptions."
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional filter by category (e.g., 'video', 'image', 'generation')."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "applyTemplate",
            "description": "Downloads and applies a selected workflow template to the canvas, replacing the current graph. Always searchTemplates first to find the correct id, source, and package.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "The unique identifier or filename of the template."
                    },
                    "source": {
                        "type": "string",
                        "enum": ["official", "custom"],
                        "description": "The source of the template: 'official' or 'custom'."
                    },
                    "package": {
                        "type": "string",
                        "description": "Required for 'custom' source: the name of the custom node package providing the template."
                    }
                },
                "required": ["id", "source"]
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
        model=OPENAI_MODEL,
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
