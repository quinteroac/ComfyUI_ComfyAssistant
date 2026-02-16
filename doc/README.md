# ComfyUI Assistant — User documentation

This folder contains user-facing documentation for the ComfyUI Assistant extension.

## Contents

| Document | Description |
|----------|-------------|
| [Installation](installation.md) | How to install the extension (Manager or manual) and build the frontend |
| [Configuration](configuration.md) | Provider wizard (required), optional `.env` fallback, first-time onboarding |
| [Personas](personas.md) | How to use personas: list, switch, create, delete; file format and manual creation |
| [Slash commands](commands.md) | Local commands for session management and quick actions |
| [User skills](skills.md) | What skills are, how to add and edit them, and how the assistant uses them |
| [Base tools](base-tools.md) | Tools the assistant can use (add/remove/connect nodes, configure widgets, prompts) and how to ask in natural language |
| [Roadmap](roadmap.md) | Development phases: what is done (0–4, 5a, 5b, 8) and what is planned (5) |

### Developer documentation ([dev_docs/](dev_docs/README.md))

| Document | Description |
|----------|-------------|
| [Architecture](dev_docs/architecture.md) | System overview, request flow, agentic loop |
| [Backend](dev_docs/backend.md) | Python modules, API endpoints, SSE streaming |
| [Context and environment](dev_docs/context-and-environment.md) | System prompt assembly, environment scanning, caching |
| [Frontend](dev_docs/frontend.md) | React components, ComfyUI integration, theme, slash commands |
| [Tools](dev_docs/tools.md) | Step-by-step guide for adding and modifying tools |
| [Standards and conventions](dev_docs/standards-and-conventions.md) | Summary of dev conventions (same as used by agents); full ref in `.agents/conventions.md`. |
| [Vibecoders guide](dev_docs/vibecoders-guide.md) | What to ask AI agents to review; prompt templates and checklist before commit/PR. |
| [Health check](dev_docs/health-check.md) | Pre-commit check report: typecheck, lint, format, tests, build, npm audit |

## Quick links

- **Quick Start**: See the project [QUICKSTART.md](../QUICKSTART.md) for a short setup guide.
- **Project README**: [README.md](../README.md) for overview, development, and project structure.
