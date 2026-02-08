# ComfyUI Assistant

AI assistant for ComfyUI that lets you control and explore workflows with natural language via a chat with tool calling.

- **Streaming chat** with real-time responses (Groq or any OpenAI-compatible provider).
- **Frontend tools**: add nodes, connect, remove, and query the workflow from the assistant tab.
- **Customization**: system prompts, user context, and editable skills.

📚 **[ComfyUI JavaScript Developer Documentation](https://docs.comfy.org/custom-nodes/js/javascript_overview)** — ComfyUI extension APIs.

## Quick Start

🚀 **[Quick Start Guide](QUICKSTART.md)** — Get the assistant running in minutes.

In the assistant tab you can type for example:

- "Add a KSampler node"
- "Create a basic text-to-image workflow"
- "What nodes are in my workflow?"

## Features

- **AI chat**: React interface (assistant-ui) with streaming, history, and markdown.
- **Tool calling**: The model uses tools that run in the browser on the ComfyUI graph.
- **Available tools**: Add nodes, remove nodes, connect nodes, get workflow info.
- **Configurable provider**: Groq by default; any OpenAI-compatible API via `OPENAI_API_BASE_URL`.
- **Rate limit control**: Configurable delay between LLM requests (`LLM_REQUEST_DELAY_SECONDS`) to avoid 429 errors.
- **Context system**: Base prompts in `system_context/`, user workspace in `user_context/` (SOUL, goals, skills).
- **TypeScript**: Typed with ComfyUI definitions and Zod for tools.

## Installation

### From ComfyUI Manager (recommended)

If published in the registry:

1. Open ComfyUI → Manager.
2. Search for "ComfyUI Assistant" (or the registered name).
3. Install.

### Manual installation

```bash
# In your ComfyUI custom_nodes directory
cd ComfyUI/custom_nodes

# Clone the repository
git clone https://github.com/YOUR_USER/ComfyUI_ComfyAssistant.git
cd ComfyUI_ComfyAssistant

# Build the frontend
cd ui
npm install
npm run build
cd ..
```

Restart ComfyUI. Without `npm run build`, the extension will not have the compiled UI in `dist/`.

## Usage

1. Open the **ComfyUI Assistant** tab in the ComfyUI sidebar.
2. Configure the API (see [Configuration](#configuration)).
3. Type in the chat; the assistant can use tools to modify the workflow.

### Configuration

Copy the example env file and edit `.env` in the node root:

```bash
cp .env.example .env
```

Main variables:

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | API key for the provider (Groq, OpenAI, etc.). **Required.** |
| `OPENAI_API_BASE_URL` | Base URL for the API (default: Groq). Change to use another provider. |
| `GROQ_MODEL` | Model (optional; default depends on provider). |
| `LLM_REQUEST_DELAY_SECONDS` | Seconds to wait before each LLM request (default `1.0`). Increase if you get 429 errors. |

After changing `.env`, restart ComfyUI.

### Assistant tools

- **Add Node**: Add a node to the canvas by type (e.g. `KSampler`, `PreviewImage`).
- **Remove Node**: Remove a node by ID.
- **Connect Nodes**: Connect one node’s output to another’s input (by IDs and slots).
- **Get Workflow Info**: Get nodes and connections in the current workflow.

### Customizing behavior

- **System prompts**: In `agent_prompts.py` the system message is built (including `system_context/` and `user_context/`).
- **Base context**: The `.md` files in `system_context/` (and its `skills/`) define role, tools, and node references.
- **User context**: In `user_context/` you have SOUL (tone/personality), goals, and user skills; the backend injects them into the system.
- **Guides**: `AGENT_PROMPTS_GUIDE.md`, `TOOLS_SETUP_GUIDE.md`, and `.agents/skills/` for development and internal docs.

## Project structure

```
ComfyUI_ComfyAssistant/
├── __init__.py              # Node entry point, API routes, streaming
├── agent_prompts.py         # System message construction
├── tools_definitions.py     # Tool definitions for the LLM
├── user_context_loader.py  # Loading system_context and user_context
├── user_context_store.py   # Store (SQLite) for rules and preferences
├── .env / .env.example     # Config (API key, URL, delay)
├── system_context/         # Base prompts (role, tools, nodes)
│   ├── 01_role.md
│   └── skills/             # System skills
├── user_context/           # User workspace (SOUL, goals, skills)
├── .agents/                # Agent documentation (skills, conventions)
├── ui/                     # React + Vite frontend
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── components/     # assistant-ui and base UI
│   │   └── tools/         # Tool definitions and implementations
│   └── package.json
├── dist/                   # Frontend build output (generated)
├── pyproject.toml
└── README.md
```

## Development

```bash
cd ui
npm install
npm run watch
```

With `watch` running, frontend changes are rebuilt; refresh the browser to see them.

### Tests

```bash
cd ui
npm test
npm run test:watch   # watch mode
```

### Publishing to ComfyUI Registry

1. Update `pyproject.toml` (name, description, `DisplayName`, `PublisherId`, etc.) for this project.
2. Install `comfy-cli`, set the registry API key, and publish with `comfy-cli publish`.
3. Optional: use the GitHub workflow (e.g. based on `.github/workflows/react-build.yml`) to publish on push.

## Resources

- [ComfyUI — JS extensions](https://docs.comfy.org/custom-nodes/js/javascript_overview)
- [assistant-ui](https://www.assistant-ui.com/)
- [Vercel AI SDK](https://sdk.vercel.ai/)
- [Groq](https://console.groq.com/docs)
- Project internal docs: `.agents/` and `AGENTS.md`

## License

MIT
