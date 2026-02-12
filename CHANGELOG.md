# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Agentic tools system with 4 core tools (addNode, removeNode, connectNodes, getWorkflowInfo)
- Complete `.agents/` documentation structure with 7 skills
- `project-context.md` for comprehensive project overview
- `conventions.md` with security-first development standards
- Documentation maintenance protocol in conventions
- Automated pre-commit checks with husky
- ComfyAPI helper class for simplified ComfyUI interactions
- Tool execution with frontend-based approach
- Structured tool definitions with Zod validation
- Tool implementations with comprehensive error handling

### Changed
- Migrated from basic template to ComfyUI Assistant implementation
- Ready to use `useLocalRuntime` for tool execution (currently using `useChatRuntime`)
- Organized skills documentation in `.agents/` as single source of truth

### Security
- All tool inputs validated with Zod schemas
- XSS prevention through React and markdown library sanitization
- API keys stored in `.env` files (excluded from git)
- Structured error handling prevents information leakage
- Access control checks before tool execution

### Documentation
- Comprehensive tool system documentation in `.agents/skills/tools/`
- Architecture diagrams and design patterns
- Implementation guides with examples
- Backend integration guide for function calling
- Tool definition best practices

## [0.1.0] - 2024-02-06

### Added
- Initial project setup based on ComfyUI React Extension Template
- React 18.2.0 + TypeScript 5.4.2 frontend with Vite
- Assistant-ui/react 0.12.9 integration for chat interface
- OpenAI-compatible provider API backend for LLM inference
- Server-Sent Events (SSE) streaming implementation
- i18n support with i18next (English + Chinese)
- Jest testing setup with React Testing Library
- ESLint + Prettier configuration
- Tailwind CSS 4.1.18 for styling
- Zustand 5.0.11 for state management
- Thread list and thread management UI components
- Markdown rendering with syntax highlighting
- Reasoning block support (`<think>` tags parsing)
- ComfyUI sidebar tab integration
- Static file serving for React app assets
- Locale files routing

### Configuration
- TypeScript strict mode enabled
- ESLint with React, TypeScript, and Prettier plugins
- Prettier with import sorting
- Jest with jsdom environment
- Vite with React plugin

### Infrastructure
- Python backend with aiohttp
- ComfyUI extension registration system
- Environment variable management with python-dotenv
- OpenAI-compatible client for OpenAI-compatible provider API
