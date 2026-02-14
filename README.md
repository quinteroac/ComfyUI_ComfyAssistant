# ComfyUI Assistant

AI assistant for ComfyUI that lets you control and explore workflows with natural language via a chat with tool calling.

- **Streaming chat** with real-time responses from any OpenAI-compatible provider.
- **Frontend tools**: add nodes, connect, remove, and query the workflow from the assistant tab.
- **Customization**: system prompts, user context, and editable skills.

📚 **[ComfyUI JavaScript Developer Documentation](https://docs.comfy.org/custom-nodes/js/javascript_overview)** — ComfyUI extension APIs.

**User documentation:** [doc/](doc/README.md) — Installation, configuration, slash commands, user skills, base tools, roadmap. **Developer docs:** [doc/dev_docs/](doc/dev_docs/README.md) — Architecture, backend, frontend, tools, standards, vibecoders guide, health check.

## Quick Start

🚀 **[Quick Start Guide](QUICKSTART.md)** — Get the assistant running in minutes.

In the assistant tab you can type for example:

- "Add a KSampler node"
- "Create a basic text-to-image workflow"
- "What nodes are in my workflow?"

## Features

- **AI chat**: React interface (assistant-ui) with streaming, history, markdown, and reasoning blocks.
- **Tool calling**: The model uses tools that run in the browser (graph) or via the backend (environment, docs, research). Tools can add/remove/connect nodes, set widgets, search installed nodes, get models, read docs, manage user skills, run or load workflows, search the web, and explore the ComfyUI Registry.
- **Modular backend architecture**: `__init__.py` delegates responsibilities to focused modules (`message_transforms.py`, `context_management.py`, `provider_streaming.py`, `cli_providers.py`, `sse_streaming.py`, `slash_commands.py`, `chat_utilities.py`) for clearer maintenance and safer refactors.
- **Slash commands**: `/help`, `/clear`, `/compact`, `/new`, `/rename`, `/session`, `/sessions`, `/skill <name>` for session management and skill activation (see [doc/commands.md](doc/commands.md)).
- **Configurable provider**: OpenAI-compatible, Anthropic API, Claude Code CLI, Gemini CLI, or Codex CLI.
- **Research capabilities**: Search the web for tutorials/workflows, fetch URL content, and discover custom nodes on the registry.
- **Rate limit control**: Configurable delay between LLM requests (`LLM_REQUEST_DELAY_SECONDS`) to avoid 429 errors.
- **Context system**: Base prompts in `system_context/`, user workspace in `user_context/` (SOUL, goals, user skills). Environment summary (nodes, models, packages) is injected when available.
- **TypeScript**: Typed with ComfyUI definitions and Zod for tools.

## Installation

The extension is not yet in the ComfyUI Manager registry. Install manually:

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

*(Once the extension is published to the ComfyUI registry, it will be installable from Manager → search for "ComfyUI Assistant".)*

## Usage

1. Open the **ComfyUI Assistant** tab in the ComfyUI bottom panel.
2. Configure the API (see [Configuration](#configuration)).
3. Type in the chat; the assistant can use tools to modify the workflow.

### Configuration

**Provider wizard (recommended):** On first use, the **Provider Wizard** opens in the Assistant tab so you can add an LLM provider (OpenAI-compatible, Anthropic, Claude Code, Codex, Gemini CLI). Settings are stored in `user_context/providers.db`. To open the wizard again later, use the slash command `/provider-settings`. See [Configuration](doc/configuration.md) for details.

**Optional `.env` fallback:** If no provider is configured in the wizard, the backend falls back to `.env` (copy from `.env.example`). Useful for automation or when you prefer file-based config. Main variables: `LLM_PROVIDER`, `OPENAI_API_KEY`, `OPENAI_API_BASE_URL`, `OPENAI_MODEL`, `ANTHROPIC_*`, `CLAUDE_CODE_*`, `CODEX_*`, `GEMINI_CLI_*`, `LLM_REQUEST_DELAY_SECONDS`, and other options listed in `.env.example`. After changing provider settings (wizard or `.env`), restart ComfyUI.

### Assistant tools

- **Graph**: Add node, remove node, connect nodes, get workflow info, set node widget value, fill prompt (CLIP text).
- **Environment**: Refresh environment cache; search installed node types; get available models by category; read documentation for nodes or topics.
- **User skills**: Create, delete, or update persistent skills (instructions the assistant remembers).
- **Workflow**: Execute current workflow (queue and wait for result); apply a full workflow from API-format JSON.
- **Research**: Web search (tutorials, workflows); fetch URL content; search ComfyUI Registry for custom nodes; get example workflows from curated library.

See [doc/base-tools.md](doc/base-tools.md) for natural-language examples and details.

### Customizing behavior

- **System prompts**: In `agent_prompts.py` the system message is built (including `system_context/` and `user_context/`).
- **Base context**: The `.md` files in `system_context/` (and its `skills/`) define role, tools, and node references.
- **User context**: In `user_context/` you have SOUL (tone/personality), goals, and user skills; the backend injects them into the system.
- **Guides**: [doc/](doc/README.md) (user docs), [doc/dev_docs/](doc/dev_docs/README.md) (developer docs: architecture, backend, frontend, tools, standards, vibecoders, health check), and [.agents/skills/](.agents/skills/) for agent/internal docs.

## Project structure

```
ComfyUI_ComfyAssistant/
├── __init__.py              # Extension entry + backend orchestrator
├── message_transforms.py    # Message format transforms (UI/OpenAI/Anthropic/CLI)
├── context_management.py    # Context truncation, history trim, token estimation
├── provider_streaming.py    # Provider-specific streaming generators
├── cli_providers.py         # CLI provider command detection
├── sse_streaming.py         # SSE protocol helpers
├── slash_commands.py        # Slash command handling
├── chat_utilities.py        # Shared chat parsing and context-limit helpers
├── agent_prompts.py         # System message assembly
├── api_handlers.py          # Environment, docs, user-context API handlers
├── tools_definitions.py     # Tool definitions for the LLM (backend)
├── user_context_loader.py  # system_context + user_context + environment
├── user_context_store.py   # SQLite: rules, preferences, onboarding
├── environment_scanner.py   # Scan nodes, packages, models; cache in user_context/environment/
├── skill_manager.py         # User skill create/list/delete/update
├── documentation_resolver.py # Resolve docs for node types and topics
├── .env.example            # Optional env fallback (wizard stores providers in user_context/providers.db)
├── system_context/         # Base prompts (role, tools, node refs)
│   ├── 01_role.md
│   └── skills/             # System skills (SKILL.md per capability)
├── user_context/           # User workspace (SOUL, goals, skills, environment cache)
├── .agents/                # Agent docs and skills (conventions, architecture, tools, etc.)
├── doc/                    # User and developer documentation
│   ├── installation.md, configuration.md, commands.md, skills.md, base-tools.md, roadmap.md
│   └── dev_docs/           # Architecture, backend, frontend, tools, standards, vibecoders, health-check
├── ui/                     # React + Vite frontend
│   ├── src/
│   │   ├── App.tsx, main.tsx
│   │   ├── components/     # assistant-ui and base UI
│   │   └── tools/          # Definitions (Zod) and implementations
│   └── package.json
├── dist/                   # Frontend build (generated; assets under dist/example_ext/)
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
3. Optional: if you use CI, add a workflow (e.g. GitHub Actions) to build the frontend and run `comfy-cli publish` on release.

## Resources

- [ComfyUI — JS extensions](https://docs.comfy.org/custom-nodes/js/javascript_overview)
- [assistant-ui](https://www.assistant-ui.com/)
- [Vercel AI SDK](https://sdk.vercel.ai/)
- [OpenAI API Docs](https://platform.openai.com/docs/api-reference)
- Project internal docs: `.agents/` and `AGENTS.md`

## License

MIT
