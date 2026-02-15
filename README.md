# ComfyUI Assistant

An AI assistant for ComfyUI: control and explore your workflows with natural language from a chat in the bottom panel. The assistant lives in **Console** — open Console, then the **ComfyUI Assistant** tab to start chatting.

- Chat with an AI that understands ComfyUI and can add nodes, connect them, run workflows, and search your environment.
- Works with any OpenAI-compatible API (or Claude Code, Codex, Gemini CLI). Configure your provider in the Assistant tab.
- You can customize the assistant with user skills, personality, and goals; the extension also ships with base skills for workflows, tools, and research.

📚 **Documentation:** [User docs](doc/README.md) (installation, configuration, commands, skills, tools) · [Developer docs](doc/dev_docs/README.md) (architecture, backend, frontend, standards).

## Quick Start

**[Quick Start Guide](QUICKSTART.md)** — Get running in a few minutes.

Open **Console** in the bottom panel, then the **ComfyUI Assistant** tab, and try:

- Ask the assistant to load a workflow for any of the models supported by ComfyUI.
- Chat about your workflow and ask for suggestions; you can ask the assistant to apply changes directly to the workflow.
- Ask the assistant to organize your workflow (layout and readability).
- Brainstorm prompts with the assistant and ask it to run the workflow with that prompt.

## Installation

1. Clone this repo into ComfyUI’s `custom_nodes` folder.
2. Build the frontend: `cd ui && npm install && npm run build && cd ..`
3. Restart ComfyUI.

Full steps and options: [doc/installation.md](doc/installation.md).

## Usage

Open the **ComfyUI Assistant** tab, set up your LLM provider (wizard on first use or [doc/configuration.md](doc/configuration.md)), and chat. The assistant can modify the workflow, run it, search nodes and models, and use the web and the ComfyUI Registry when needed.

- **Commands:** Slash commands like `/help`, `/clear`, `/new`, `/skill` — see [doc/commands.md](doc/commands.md).
- **What the assistant can do:** Graph actions, environment search, user skills, workflow execution, research — see [doc/base-tools.md](doc/base-tools.md).
- **Customization:** System and user context, skills, SOUL, goals — see [doc/](doc/README.md).

## Recommended providers

- **Claude Opus 4** — Best for complex tasks (workflow design, multi-step reasoning). More expensive; use the Anthropic API or Open Router.
- **Gemini** — Good for most day-to-day tasks. Use Gemini CLI or the Open Router API.
- **Grok** — Great for prompt ideas and creative brainstorming. Use the x.ai API or Open Router.

See [doc/configuration.md](doc/configuration.md) for how to add and switch providers.

## Development

Frontend: `cd ui && npm run watch` (rebuilds on change; refresh the browser). Tests: `cd ui && npm test`.  
Architecture, backend, frontend, tools, and conventions: [doc/dev_docs/](doc/dev_docs/README.md).

## Resources

- [ComfyUI — JavaScript extensions](https://docs.comfy.org/custom-nodes/js/javascript_overview)
- [assistant-ui](https://www.assistant-ui.com/) · [Vercel AI SDK](https://sdk.vercel.ai/)

## Acknowledgements

ComfyUI Assistant builds on the following projects and libraries:

| Project | Purpose | Links |
|--------|---------|-------|
| **ComfyUI** | Host UI and workflow engine | [Docs](https://docs.comfy.org/) · [GitHub](https://github.com/comfyanonymous/ComfyUI) |
| **assistant-ui** | Chat UI and runtime | [Docs](https://www.assistant-ui.com/) · [GitHub](https://github.com/assistant-ui/assistant-ui) |
| **Vercel AI SDK** | LLM integration and streaming | [Docs](https://sdk.vercel.ai/) · [GitHub](https://github.com/vercel/ai) |
| **React** | UI framework | [Docs](https://react.dev/) |
| **Tailwind CSS** | Styling | [Docs](https://tailwindcss.com/) |
| **Vite** | Build tool | [Docs](https://vitejs.dev/) |
| **TypeScript** | Typing | [Docs](https://www.typescriptlang.org/) |
| **Zod** | Schema and validation | [Docs](https://zod.dev/) |
| **Radix UI** | Accessible components | [Docs](https://www.radix-ui.com/) |
| **Zustand** | State management | [Docs](https://zustand.docs.pmnd.rs/) |
| **OpenAI Python** | Backend LLM client (OpenAI-compatible APIs) | [GitHub](https://github.com/openai/openai-python) |
| **python-dotenv** | Environment config | [GitHub](https://github.com/theskumar/python-dotenv) |

## License

MIT
