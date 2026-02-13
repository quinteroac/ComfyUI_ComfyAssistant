# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Official ComfyUI Manager installation support.
- Multi-provider UI for managing LLM configurations.
- Enhanced security and sandboxing for third-party node content.
- Internationalization (i18n) for AI responses.

## [0.2.0] - 2026-02-12

### Added
- **Research Tools (Phase 8)**:
  - `webSearch`: Search the web via SearXNG or DuckDuckGo.
  - `fetchWebContent`: Extract content and workflows from URLs.
  - `searchNodeRegistry`: Discover custom nodes on comfyregistry.org.
  - `getExampleWorkflow`: Access library of curated example workflows.
- **Slash Commands & Session Management (Phase 5b)**:
  - New commands: `/help`, `/clear`, `/compact`, `/new`, `/rename`, `/session`, `/sessions`, `/skill`.
  - Inline autocomplete for slash commands.
  - Named sessions and persistent thread management.
- **Terminal UI & Bottom Panel (Phase 5a)**:
  - New bottom panel integration for the assistant.
  - Terminal-style aesthetic with monospace fonts and compact layout.
  - Horizontal thread/session navigation bar.
- **Workflow Execution (Phase 4)**:
  - `executeWorkflow`: Run current graph and return real-time results/images.
  - `applyWorkflowJson`: Load complex API-format workflows in one call.
  - Real-time execution monitoring and error reporting.
- **Environment Awareness (Phase 3)**:
  - `refreshEnvironment`: Rescan nodes, packages, and models.
  - `searchInstalledNodes`: Smart search for available node types.
  - `readDocumentation`: Fetch node-specific or general ComfyUI documentation.
  - `createSkill`: Agent-driven creation of persistent user preferences.
- **Node Configuration (Phase 2)**:
  - `setNodeWidgetValue`: Programmatic control over node parameters (steps, cfg, etc.).
  - `fillPromptNode`: Shorthand for setting CLIPTextEncode values.

### Changed
- Reorganized system prompt assembly into modular components (`agent_prompts.py`).
- Extracted API handlers to a dedicated module (`api_handlers.py`).
- Improved tool execution flow with direct `window.app` access in the frontend.

## [0.1.0] - 2024-02-06

### Added
- Initial project setup and architecture.
- Assistant-ui/react integration with SSE streaming.
- Core graph tools: `addNode`, `removeNode`, `connectNodes`, `getWorkflowInfo`.
- User context system: SQLite store for rules, preferences, and onboarding.
- Manual skills support via `user_context/skills/`.
- OpenAI-compatible provider backend for LLM inference.
- Basic i18n and testing boilerplate.
