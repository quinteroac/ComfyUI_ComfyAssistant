# ComfyUI Assistant - Project Context

## Project Overview

**Name**: ComfyUI Assistant (ComfyUI_ComfyAssistant)  
**Type**: ComfyUI Custom Node Extension with AI Assistant  
**Base**: ComfyUI React Extension Template  
**Version**: 0.2.0  
**License**: MIT

ComfyUI Assistant is an AI-powered extension for ComfyUI that provides an intelligent chat interface with agentic capabilities to interact with ComfyUI workflows. It extends the ComfyUI React Extension Template with a complete assistant-ui implementation and a tools system for workflow manipulation.

## Purpose

This extension enables users to:
- Chat with an AI assistant about their ComfyUI workflows
- Manipulate workflows through natural language commands
- Get information about current workflow state
- Add, remove, and connect nodes programmatically
- Learn ComfyUI through interactive assistance

## Architecture

### Frontend Stack

- **Framework**: React 18.2.0 + TypeScript 5.4.2
- **Build Tool**: Vite 5.2.10
- **UI Library**: assistant-ui/react 0.12.9
- **AI Integration**: Vercel AI SDK 6.0.73
- **Styling**: Tailwind CSS 4.1.18
- **State Management**: Zustand 5.0.11
- **Validation**: Zod 3.25.76
- **i18n**: i18next 23.10.2
- **Testing**: Jest 29.7.0 + React Testing Library 16.3.0

### Backend Stack

- **Runtime**: Python 3.x
- **Web Framework**: aiohttp (via ComfyUI's server)
- **LLM Provider**: OpenAI-compatible provider API (OpenAI-compatible)
- **Streaming**: Server-Sent Events (SSE)
- **Environment**: python-dotenv 1.0.0
- **Architecture pattern**: Modular backend decomposition (Phases 1-8) with `__init__.py` as orchestrator
- **Module categories**: Pure Transformation, Provider, Command, Storage, API modules
- **Reference**: See `.agents/conventions.md` → `Backend Module Organization` for module templates and rules

### Integration Points

1. **ComfyUI Integration**
   - Custom node extension loaded by ComfyUI
   - Access to `window.app` (ComfyUI's JavaScript API)
   - Bottom panel tab registration (Phase 5a)
   - Menu items and commands

2. **AI Integration**
   - OpenAI-compatible provider API for LLM inference
   - OpenAI-compatible client (openai>=1.0.0)
   - Streaming responses via SSE
   - Function calling / tool use

3. **Tools System**
   - Frontend-executed tools via `useLocalRuntime`
   - Direct access to ComfyUI graph API
   - Backend declares tools for LLM
   - Bidirectional communication (frontend ↔ backend ↔ LLM)

## Directory Structure

```
ComfyUI_ComfyAssistant/
├── .agents/                    # Agent skills and documentation
│   ├── skills/                 # 15 skill modules
│   │   ├── assistant-ui/       # assistant-ui architecture
│   │   ├── primitives/         # UI primitives
│   │   ├── runtime/            # Runtime patterns
│   │   ├── setup/              # Setup guides
│   │   ├── streaming/          # Streaming protocols
│   │   ├── thread-list/        # Thread management
│   │   ├── tools/              # Agentic tools system ⭐
│   │   ├── architecture-overview/
│   │   ├── backend-architecture/
│   │   ├── backend-tools-declaration/
│   │   ├── documentation/
│   │   ├── environment-and-models/
│   │   ├── patterns-and-conventions/
│   │   ├── system-and-user-context/
│   │   └── ui-integration/
│   └── *.md                    # Agent investigation or one-off notes (e.g. investigation-tool-order.md)
│
├── system_context/             # Base system prompt (read-only; top-level .md then skills/*/SKILL.md)
│   ├── 01_role.md
│   ├── skills/                 # Base capabilities (Agent Skills standard: dir/SKILL.md with frontmatter)
│   │   ├── 01_base_tools/SKILL.md
│   │   ├── 02_tool_guidelines/SKILL.md
│   │   ├── 03_node_reference/SKILL.md
│   │   ├── 04_environment_tools/SKILL.md
│   │   ├── 05_workflow_execution/SKILL.md
│   │   ├── 06_research_tools/SKILL.md
│   │   ├── 07_workflow_guardrails/SKILL.md
│   │   ├── 08_comfyui_examples_source/SKILL.md
│   │   ├── 09_template_library/SKILL.md
│   │   └── 17_model_loading_rules/SKILL.md
│   └── README.md
│
├── user_context/               # User workspace; writable by backend only
│   ├── context.db              # SQLite: rules, preferences, onboarding flag
│   ├── providers.db            # SQLite: provider configs + active provider
│   ├── SOUL.md                 # Personality / tone (from onboarding or manual edit)
│   ├── goals.md                # User goals and experience level
│   ├── environment/            # Cached environment scan data (Phase 3)
│   │   ├── installed_nodes.json # All node types with inputs/outputs
│   │   ├── custom_nodes.json   # Custom node packages
│   │   ├── models.json         # Available models by category
│   │   └── summary.json        # Brief summary for prompt injection
│   ├── skills/                 # One dir per user skill (SKILL.md with YAML frontmatter)
│   │   └── <slug>/SKILL.md     # e.g. use-preview-image/SKILL.md
│   └── logs/                   # Optional: daily JSONL conversation logs (when COMFY_ASSISTANT_ENABLE_LOGS=1)
│
├── ui/                         # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── assistant-ui/  # Chat UI components
│   │   │   └── ui/            # Base UI components (shadcn-style)
│   │   ├── tools/             # Agentic tools implementation ⭐
│   │   │   ├── definitions/   # Tool schemas (Zod)
│   │   │   ├── implementations/ # Tool execution logic
│   │   │   ├── index.ts       # Tool registry
│   │   │   └── types.ts       # Shared types
│   │   ├── lib/
│   │   │   └── utils.ts       # Utilities
│   │   ├── App.tsx            # Main application
│   │   └── main.tsx           # Entry point
│   ├── public/locales/        # i18n translations
│   └── package.json
│
├── __init__.py                # Python backend entry point
├── agent_prompts.py           # Assembles system message: system_context + environment + user_context
├── user_context_store.py     # SQLite store for rules, preferences, onboarding
├── provider_store.py         # SQLite store for provider configs (providers.db)
├── provider_manager.py       # Runtime provider config selection + connection tests
├── message_transforms.py     # Pure transformations: UI/OpenAI/Anthropic/CLI message formats
├── context_management.py     # Context truncation, history trim, token estimation, compaction
├── provider_streaming.py     # Provider streaming generators (OpenAI/Anthropic/CLI adapters)
├── cli_providers.py          # CLI provider command detection utilities
├── sse_streaming.py          # SSE headers and stream event formatting helpers
├── slash_commands.py         # Slash command handling (/provider, /skill)
├── chat_utilities.py         # Shared chat helpers and context-too-large detection
├── user_context_loader.py     # load_system_context, load_user_context, load_environment_summary
├── tools_definitions.py       # Backend tool declarations (single source of truth) ⭐
├── environment_scanner.py     # Scan installed nodes, packages, models (Phase 3)
├── skill_manager.py           # Create/list/delete user skills (Phase 3)
├── documentation_resolver.py  # Resolve docs for node types and topics (Phase 3)
├── conversation_logger.py     # Conversation logging to user_context/logs/ (optional)
├── api_handlers.py            # Extracted API endpoint handlers (Phase 3 + Phase 8)
├── web_search.py              # Web search provider abstraction (Phase 8)
├── web_content.py             # URL content extraction (Phase 8)
├── node_registry.py           # ComfyUI Registry API client (Phase 8)
├── doc/                       # User and developer documentation
│   ├── README.md              # Index
│   ├── installation.md       # Install (Manager / manual)
│   ├── configuration.md      # API, onboarding, user context
│   ├── skills.md             # User skills usage
│   ├── base-tools.md         # Base tools and natural language
│   ├── roadmap.md            # Development phases (done + planned)
│   └── dev_docs/             # Developer docs (standards + vibecoders)
│       ├── README.md          # Index
│       ├── standards-and-conventions.md  # Summary; full: .agents/conventions.md
│       └── vibecoders-guide.md           # What to ask agents to review
├── .env.example               # Environment template
├── pyproject.toml             # Python project metadata
└── README.md                  # Documentation
```

### System and user context (injection order)

The system message is built as **system_context + user_context + skills** (same mechanism for both):

1. **system_context/** — Base system prompt. Read-only `.md` files concatenated in sorted filename order (e.g. `01_role_and_capabilities.md`, `02_tool_guidelines.md`, `03_node_reference.md`). Loaded by `user_context_loader.load_system_context(system_context_path)`. If missing or empty, a minimal fallback prompt is used.
2. **user_context/** — User workspace (Phase 1); writable by backend. Injected after system context (see below).
3. **Skills** — Loaded from `user_context/skills/*.md` and included in the user context block (see “User context workspace” below).

### User context workspace (Phase 1)

The **user_context/** directory is the assistant’s writable workspace (created on first use). It is separate from **.agents/** (project docs). Backend only writes here; the UI agent reads via injected system message.

- **context.db** — SQLite: `rules` (name, rule_text), `preferences` (key/value), `meta` (e.g. onboarding_done).
- **SOUL.md**, **goals.md** — Plain markdown; set by first-time onboarding or manual edit. Injected as “Personality” and “Goals” in the system prompt.
- **skills/** — One directory per user skill: `skills/<name>/SKILL.md` per [Agent Skills](https://agentskills.io) standard (see [Claude Code skills](https://code.claude.com/docs/en/skills)). SKILL.md has YAML frontmatter (`name`, `description`) and a markdown body. Legacy flat `skills/<slug>.md` files are still supported. Skills can be created manually or by the agent via the `createSkill` tool (Phase 3). Full text or summaries by size; see `user_context_loader.py`.
- **environment/** — Cached environment scan data (Phase 3). Generated by `environment_scanner.scan_environment()`. Contains `installed_nodes.json`, `custom_nodes.json`, `models.json`, and `summary.json`. Auto-scanned on startup; refreshed via `refreshEnvironment` tool. Node search (GET `/api/environment/nodes`) uses this cache first; when the cache returns no matches, the backend uses ComfyUI's GET `/object_info` API (or `scan_installed_node_types()` if the API is unavailable).

## Key Features

### 1. AI Chat Interface

- Built with assistant-ui/react
- Streaming responses from OpenAI-compatible provider
- Message threading and history
- Markdown rendering with syntax highlighting
- Support for reasoning blocks (`<think>` tags)
- Console-style UI with thread list UI hidden (sessions intended for slash-command management)

### 2. Agentic Tools System

**Available Tools:**
- `addNode`: Add nodes to the workflow
- `removeNode`: Remove nodes by ID
- `connectNodes`: Connect two nodes
- `getWorkflowInfo`: Query workflow state (including widget names/values with `includeNodeDetails`)
- `setNodeWidgetValue`: Set any widget value on a node (steps, cfg, seed, sampler_name, etc.)
- `fillPromptNode`: Set the text of a CLIPTextEncode node (shorthand for setNodeWidgetValue)
- `refreshEnvironment`: Rescan installed nodes, packages, and models (Phase 3)
- `searchInstalledNodes`: Search installed node types by name, category, package, display name, or description; cache-first, then ComfyUI GET `/object_info` API fallback when cache has no results (Phase 3)
- `getAvailableModels`: List installed model filenames by category (checkpoints, loras, vae, etc.); used for model recommendations (e.g. "what do you recommend for hyperrealistic?") (Phase 3)
- `readDocumentation`: Fetch documentation for a node type or topic (Phase 3)
- `createSkill`: Create a persistent user skill from a remembered instruction (Phase 3)
- `deleteSkill`: Delete a user skill by slug (Phase 3)
- `updateSkill`: Update a user skill by slug — name, description, or instructions (Phase 3)
- `getUserSkill`: Fetch a user skill's full instructions by slug (on demand)
- `listUserSkills`: List all user skills with name, description, and slug
- `listSystemSkills`: List model-specific system skills (e.g. Flux, SDXL) available on demand
- `getSystemSkill`: Fetch a model-specific system skill's instructions by slug (on demand)
- `executeWorkflow`: Queue the current workflow, wait for completion, return status + outputs (Phase 4)
- `applyWorkflowJson`: Load a complete workflow (API format or frontend format with nodes/links), replacing the current graph (Phase 4)
- `getExampleWorkflow`: Fetch example workflows extracted from ComfyUI_examples by category (Phase 8)
- `webSearch`: Search the web for ComfyUI resources, tutorials, workflows (Phase 8)
- `fetchWebContent`: Fetch and extract content from a URL, detect embedded workflows (Phase 8)
- `searchNodeRegistry`: Search the ComfyUI Registry for custom node packages (Phase 8)
- `searchTemplates`: Search official and community workflow templates by title, description, or category (e.g. wan, flux). Use to find a starting point for complex workflows.
- `applyTemplate`: Download and apply a selected workflow template to the canvas. Replaces the current graph.

**Architecture:**
- Tools defined with Zod schemas (frontend)
- Tools declared in OpenAI format (backend)
- Execution happens in frontend (direct access to `window.app`)
- Results flow back to LLM for continued conversation

**Agent Intelligence:**
- System prompts guide LLM behavior (`agent_prompts.py`)
- Instructions on when and how to use each tool
- Common ComfyUI node types reference
- Few-shot examples for improved performance
- Customizable personality and communication style

### 3. ComfyUI Integration

- Bottom panel tab for chat interface (terminal-style UI, Phase 5a)
- **Slash commands** (Phase 5b): `/help`, `/clear`, `/compact [keep]`, `/new`, `/rename <name>`, `/session <id|index|name>`, `/sessions`, `/skill <name>` (backend-handled), `/provider-settings`, `/provider list`, `/provider set <name>` (backend-handled); inline autocomplete when typing `/`
- Named sessions via `/rename` or Rename option in thread tab dropdown
- Direct access to ComfyUI graph via `window.app`
- Canvas manipulation (add/remove/connect nodes)
- Real-time workflow monitoring

### 4. Development Features

- Hot reload with Vite watch mode
- TypeScript with strict type checking
- ESLint + Prettier code formatting
- Jest unit testing setup
- i18n support (English + Chinese)

## Technology Decisions

### Why assistant-ui/react?

- Purpose-built for AI chat interfaces
- Handles streaming, threading, tool calling out of the box
- Compatible with Vercel AI SDK
- Extensive customization options

### Why OpenAI-compatible provider?

- Fast inference (optimized LLM serving)
- OpenAI-compatible API
- Supports function calling / tool use
- Free tier for development

### Why Frontend Tool Execution?

- Direct access to `window.app` (ComfyUI API)
- No need to expose ComfyUI API over network
- Lower latency (no extra network hop)
- Better security (no backend → ComfyUI connection needed)

### Why Zod?

- Runtime validation + TypeScript types
- Self-documenting schemas
- Easy to sync with backend OpenAI format
- Excellent DX with type inference

## Configuration

**Provider wizard (primary):** Users configure LLM providers (OpenAI-compatible, Anthropic, Claude Code, Codex, Gemini CLI) via the Provider Wizard in the Assistant tab (or `/provider-settings`). Settings are stored in `user_context/providers.db`. See [doc/configuration.md](../doc/configuration.md).

**Backend `.env` (fallback):** If no provider is set in the wizard, the backend falls back to `.env` (see `.env.example`). Used for automation or file-based config.

### Environment Variables

**Backend** (`.env` — optional fallback):
```bash
LLM_PROVIDER=openai                  # Optional: openai, anthropic, claude_code, codex, gemini_cli
OPENAI_API_KEY=gsk_xxx               # OpenAI-compatible provider API key
OPENAI_API_BASE_URL=https://...      # Optional: OpenAI-compatible API URL
OPENAI_MODEL=llama3-70b-8192         # Optional: OpenAI-compatible model
ANTHROPIC_API_KEY=sk-ant-...         # Optional: Anthropic API key (required for anthropic provider)
ANTHROPIC_MODEL=claude-sonnet-4-5    # Optional: Anthropic model name
ANTHROPIC_BASE_URL=https://api.anthropic.com # Optional: Anthropic API URL
ANTHROPIC_MAX_TOKENS=4096            # Optional: Anthropic max output tokens
CLAUDE_CODE_COMMAND=claude           # Optional: claude_code CLI executable
CLAUDE_CODE_MODEL=sonnet             # Optional: claude_code model alias
CODEX_COMMAND=codex                  # Optional: codex CLI executable
CODEX_MODEL=o3                       # Optional: codex model alias
GEMINI_CLI_COMMAND=gemini            # Optional: gemini CLI executable
GEMINI_CLI_MODEL=auto                # Optional: gemini model name
CLI_PROVIDER_TIMEOUT_SECONDS=180     # Optional: timeout for CLI provider subprocesses
SEARXNG_URL=http://localhost:8080  # Optional: SearXNG instance for web search (Phase 8)
COMFY_ASSISTANT_DEBUG_CONTEXT=0    # Optional: when "1", emit context pipeline debug metrics (X-ComfyAssistant-Context-Debug header, context-debug SSE event)
COMFY_ASSISTANT_LOG_LEVEL=INFO           # Optional: DEBUG, INFO, WARNING, ERROR. Default: INFO
COMFY_ASSISTANT_ENABLE_LOGS=0             # Optional: when "1", save conversation logs to user_context/logs/
LLM_REQUEST_DELAY_SECONDS=1.0             # Optional: delay before each LLM request (avoid 429)
LLM_SYSTEM_CONTEXT_MAX_CHARS=12000       # Optional: max chars from system_context per request
LLM_USER_CONTEXT_MAX_CHARS=2500          # Optional: max chars for user context block
LLM_HISTORY_MAX_MESSAGES=24              # Optional: max non-system messages per request
LLM_TOOL_RESULT_KEEP_LAST_ROUNDS=2        # Optional: full tool-result rounds kept; older get placeholder
```
OpenAI-compatible providers use `OPENAI_*`. Anthropic provider uses `ANTHROPIC_API_KEY`.
ANTHROPIC_AUTH_TOKEN is for Claude Code CLI only; this backend uses ANTHROPIC_API_KEY.
`claude_code`, `codex`, and `gemini_cli` providers use local authenticated CLI executables.

**Frontend** (`ui/.env.local`):
```bash
# Currently none required (inherits from backend)
```

### Build Configuration

- **Frontend Build**: `npm run build` → `dist/example_ext/`
- **Watch Mode**: `npm run watch` (auto-rebuild on changes)
- **TypeScript**: Strict mode enabled
- **Target**: ES2020, module resolution: bundler

## Development Workflow

### Standard Development

1. Start ComfyUI
2. Navigate to `ui/` directory
3. Run `npm run watch`
4. Edit source files
5. Refresh browser (changes auto-rebuild)

### Adding New Tools

1. Create definition in `ui/src/tools/definitions/`
2. Create implementation in `ui/src/tools/implementations/`
3. Register in `ui/src/tools/index.ts`
4. Add to `tools_definitions.py` (backend)
5. Rebuild frontend

### Testing

```bash
cd ui
npm test              # Run all tests
npm run test:watch    # Watch mode
```

## API Endpoints

### POST /api/chat

**Purpose**: Main chat endpoint for AI assistant

**Request**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Add a KSampler node"
    }
  ]
}
```

**Response**: Server-Sent Events (SSE) stream
```
data: {"type": "start", "messageId": "msg_xxx"}
data: {"type": "text-delta", "id": "text_xxx", "delta": "I'll add"}
data: {"type": "tool-call-delta", "id": "tool_xxx", "name": "addNode", ...}
data: [DONE]
```

**Behavior Control**:
- System prompts from `agent_prompts.py` are automatically injected
- Environment summary injected when cached scan data exists
- Guides LLM on when/how to use tools
- Includes ComfyUI domain knowledge
- Customizable via `get_system_message()` variants

### Phase 3 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/environment/scan` | POST | Trigger full environment scan |
| `/api/environment/summary` | GET | Brief summary for prompt injection |
| `/api/environment/nodes` | GET | Search installed node types (`?q=...&category=...&limit=20`) |
| `/api/environment/models` | GET | List models by category |
| `/api/environment/packages` | GET | List custom node packages |
| `/api/environment/docs` | GET | Fetch documentation (`?topic=...&source=any`) |
| `/api/user-context/skills` | POST | Create skill (`{name, description, instructions}`) |
| `/api/user-context/skills` | GET | List all user skills |

### Phase 8 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/research/search` | POST | Web search (`{query, maxResults?, timeRange?}`) |
| `/api/research/fetch` | POST | Fetch URL content (`{url, extractWorkflow?}`) |
| `/api/research/registry` | GET | Search ComfyUI Registry (`?q=...&limit=...&page=...`) |

## Skills System (.agents/)

The `.agents/` directory contains comprehensive documentation and guides for AI agents working on this project:

- **architecture-overview**: System flow and architecture
- **assistant-ui**: Architecture and component patterns
- **backend-architecture**: Python backend, API, SSE
- **backend-tools-declaration**: Tool definitions and backend declaration
- **documentation**: When and how to update docs
- **environment-and-models**: Environment scanning and models
- **patterns-and-conventions**: Code and convention quick reference
- **primitives**: UI primitive components usage
- **runtime**: Runtime patterns and state management
- **setup**: Setup and configuration guides
- **streaming**: Streaming protocols and data formats
- **system-and-user-context**: System prompts and user context
- **thread-list**: Thread management patterns
- **tools**: Agentic tools system
- **ui-integration**: ComfyUI extension, panel, slash commands

Each skill includes:
- `SKILL.md`: Main skill documentation
- `references/`: Detailed reference materials

## Dependencies

### Critical Frontend Dependencies

- `@assistant-ui/react` - Chat UI framework
- `@assistant-ui/react-ai-sdk` - AI SDK integration
- `ai` - Vercel AI SDK
- `@comfyorg/comfyui-frontend-types` - ComfyUI types
- `zod` - Schema validation
- `react` + `react-dom` - UI framework

### Critical Backend Dependencies

- `openai` - OpenAI-compatible client (for OpenAI-compatible provider)
- `python-dotenv` - Environment configuration
- `aiohttp` - Web server (via ComfyUI)
- `ddgs` - Web search fallback (Phase 8)
- `beautifulsoup4` - HTML content extraction (Phase 8)
- `crawl4ai` - Optional: advanced content extraction via Playwright (Phase 8)

## Known Limitations

1. **Tool Execution**: Tools can only access what's available in `window.app`
2. **Model Support**: Function calling requires OpenAI-compatible provider models with tool support
3. **Streaming**: Complex tool calling streams require careful SSE handling
4. **ComfyUI Version**: Requires ComfyUI with modern frontend (window.app available)

## Future Enhancements

- [x] Workflow execution and generation (executeWorkflow, applyWorkflowJson — Phase 4)
- [x] Node widget manipulation (setNodeWidgetValue, fillPromptNode — Phase 2)
- [x] Environment awareness (refreshEnvironment, searchInstalledNodes, readDocumentation — Phase 3)
- [x] Agent-driven skill creation (createSkill — Phase 3)
- [x] Research tools: web search, content extraction, node registry (Phase 8)
- [ ] Workflow templates and presets
- [ ] Multi-turn tool calling
- [ ] User confirmations for destructive actions
- [ ] Tool execution history
- [ ] Custom model support (beyond OpenAI-compatible provider)

## Resources

- **ComfyUI Docs**: https://docs.comfy.org/
- **assistant-ui Docs**: https://www.assistant-ui.com/
- **AI SDK Docs**: https://sdk.vercel.ai/
- **OpenAI-compatible provider Docs**: https://console.provider.com/docs
- **Project Skills**: `.agents/skills/` (comprehensive guides)

## Maintenance Notes

- Rebuild frontend after tool changes: `cd ui && npm run build`
- Restart ComfyUI after backend changes
- Keep tool definitions synced (frontend ↔ backend)
- Update version in `pyproject.toml` for releases
