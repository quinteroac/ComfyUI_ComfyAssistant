# ComfyUI Assistant - Project Context

## Project Overview

**Name**: ComfyUI Assistant (ComfyUI_ComfyAssistant)  
**Type**: ComfyUI Custom Node Extension with AI Assistant  
**Base**: ComfyUI React Extension Template  
**Version**: 0.1.0  
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
- **LLM Provider**: Groq API (OpenAI-compatible)
- **Streaming**: Server-Sent Events (SSE)
- **Environment**: python-dotenv 1.0.0

### Integration Points

1. **ComfyUI Integration**
   - Custom node extension loaded by ComfyUI
   - Access to `window.app` (ComfyUI's JavaScript API)
   - Sidebar tab registration
   - Menu items and commands

2. **AI Integration**
   - Groq API for LLM inference
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
│   └── skills/                 # 7 skill modules
│       ├── assistant-ui/       # assistant-ui architecture
│       ├── primitives/         # UI primitives
│       ├── runtime/            # Runtime patterns
│       ├── setup/              # Setup guides
│       ├── streaming/          # Streaming protocols
│       ├── thread-list/        # Thread management
│       └── tools/              # Agentic tools system ⭐
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
├── agent_prompts.py           # System prompts for LLM agent ⭐
├── tools_definitions.py       # Backend tool declarations ⭐
├── .env.example               # Environment template
├── pyproject.toml             # Python project metadata
└── README.md                  # Documentation
```

## Key Features

### 1. AI Chat Interface

- Built with assistant-ui/react
- Streaming responses from Groq
- Message threading and history
- Markdown rendering with syntax highlighting
- Support for reasoning blocks (`<think>` tags)

### 2. Agentic Tools System

**Available Tools:**
- `addNode`: Add nodes to the workflow
- `removeNode`: Remove nodes by ID
- `connectNodes`: Connect two nodes
- `getWorkflowInfo`: Query workflow state

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

- Sidebar tab for chat interface
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

### Why Groq?

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

### Environment Variables

**Backend** (`.env`):
```bash
GROQ_API_KEY=gsk_xxx              # Required: API key for the LLM provider
OPENAI_API_BASE_URL=https://...   # Optional: OpenAI-compatible API URL (default: Groq)
GROQ_MODEL=llama3-70b-8192        # Optional: Model name
```
Use `OPENAI_API_BASE_URL` to point to any OpenAI-compatible provider (Groq, OpenAI, Together, Ollama, etc.).

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
- Guides LLM on when/how to use tools
- Includes ComfyUI domain knowledge
- Customizable via `get_system_message()` variants

## Skills System (.agents/)

The `.agents/` directory contains comprehensive documentation and guides for AI agents working on this project:

- **assistant-ui**: Architecture and component patterns
- **primitives**: UI primitive components usage
- **runtime**: Runtime patterns and state management
- **setup**: Setup and configuration guides
- **streaming**: Streaming protocols and data formats
- **thread-list**: Thread management patterns
- **tools**: Complete agentic tools system documentation

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

- `openai` - OpenAI-compatible client (for Groq)
- `python-dotenv` - Environment configuration
- `aiohttp` - Web server (via ComfyUI)

## Known Limitations

1. **Tool Execution**: Tools can only access what's available in `window.app`
2. **Model Support**: Function calling requires Groq models with tool support
3. **Streaming**: Complex tool calling streams require careful SSE handling
4. **ComfyUI Version**: Requires ComfyUI with modern frontend (window.app available)

## Future Enhancements

- [ ] More workflow manipulation tools (save, load, execute)
- [ ] Node widget manipulation
- [ ] Workflow templates and presets
- [ ] Multi-turn tool calling
- [ ] User confirmations for destructive actions
- [ ] Tool execution history
- [ ] Custom model support (beyond Groq)

## Resources

- **ComfyUI Docs**: https://docs.comfy.org/
- **assistant-ui Docs**: https://www.assistant-ui.com/
- **AI SDK Docs**: https://sdk.vercel.ai/
- **Groq Docs**: https://console.groq.com/docs
- **Project Skills**: `.agents/skills/` (comprehensive guides)

## Maintenance Notes

- Rebuild frontend after tool changes: `cd ui && npm run build`
- Restart ComfyUI after backend changes
- Keep tool definitions synced (frontend ↔ backend)
- Update version in `pyproject.toml` for releases
