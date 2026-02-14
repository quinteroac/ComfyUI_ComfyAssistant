# ComfyUI Assistant — non-functional requirements

This document outlines **non-functional** requirements: how the assistant is installed, configured, secured, and how it behaves in terms of performance, usability, and compatibility. It complements the [features](comfyui_assistant_features.md) and [design](comfyui_assistant_design.md) documents.

---

## Installability and distribution

- **Installation via ComfyUI Manager** — The custom node must be installable through **ComfyUI Manager** so users can add it without manual cloning or copying. The package should expose the correct metadata (e.g. `pyproject.toml` / manifest) so Manager can install and update it.
- **No mandatory external services at install time** — Installation must not require signing up for or configuring external services. Optional features (e.g. embeddings, specific LLM providers) may require later configuration.

---

## Configurability (LLM and providers)

- **Multiple LLM providers** — The assistant must support **multiple LLM providers** (OpenAI, OpenAI-compatible APIs, local models, etc.). The user should be able to add, switch, and configure providers from a single place (e.g. settings or a dedicated UI).
- **OpenAI API compatibility** — All configured providers must be usable via the **OpenAI API** (same request/response shape). Providers that expose an OpenAI-compatible endpoint (e.g. LiteLLM, Ollama with compatibility layer, Azure OpenAI, Grok, Claude via proxy) can be added by setting base URL and API key (or equivalent). This keeps the client code simple and allows swapping models without changing the integration.
- **Secrets and credentials** — API keys and other secrets must not be hardcoded. They must be configurable via environment variables, a local config file (e.g. `.env` in the workspace or ComfyUI root), or a secure settings mechanism that does not commit secrets to version control. The documentation must explain how to set each provider.

---

## Security

- **Read-only outside workspace** — The back agent may **read** the ComfyUI installation (e.g. `custom_nodes/`, `models/`, other nodes’ `.agents/`) but must **not modify** it. The only writable area for the assistant is its **own workspace** (e.g. under the custom node: user context, rules, `.agents/` shared context, caches). See [design](comfyui_assistant_design.md).
- **Untrusted content from custom nodes** — Content read from third-party custom nodes’ `.agents/` or `.agents/skills/` must be treated as **untrusted** (risk of prompt injection or malicious instructions). It must be sanitized or constrained before being injected into the UI or back agent context.
- **Minimal read** — The back agent should read only what is strictly needed to build the environment context (installed nodes, models, merged docs), not arbitrary files from the system.

---

## Usability and accessibility

- **Multi-language** — The agent’s responses (and any generated UI text) must respect the **user’s language** when possible. The user can specify a preferred language; the assistant should answer in that language consistently. This supports both technical and non-technical users in their preferred locale.
- **First-time onboarding** — On first use, the user should be able to define the assistant’s personality and answer a short set of questions (goals, experience level, preferences). This is persisted so that later sessions do not require repeating it. Onboarding can be skipped or deferred with a neutral default. See [design](comfyui_assistant_design.md#14-first-time-onboarding-openclaw-style).

---

## Performance and context

- **Documentation on demand** — To avoid exhausting the context window, documentation (ComfyUI OOB or custom nodes) must be loaded **on demand**: only the excerpts relevant to the current request are fetched and injected. See [tools](comfyui_assistant_tools.md) (`read_documentation`).
- **Reasonable latency** — Tool calls (add node, connect, read workflow, etc.) should complete in a time that keeps the conversation fluid. Long-running operations (e.g. `refresh_environment`, `execute_workflow`) may stream progress or status back to the UI so the user is informed.
- **No hard dependency on embeddings** — User context and retrieval must work **without** an embedding API. When embeddings are available, they can be used as an optional layer; when not, a fixed window of recent messages or a short summary (e.g. in SQLite or a .md file) must suffice. See [design](comfyui_assistant_design.md#13-semantic-retrieval-optional--embeddings).

---

## Compatibility and maintainability

- **Stable tool and skill contracts** — Tools (names, parameters, behavior) and the structure of skills (e.g. in `.agents/skills/`) should be documented and kept stable so that custom node authors and users can rely on them. Breaking changes should be versioned and described (e.g. in a CHANGELOG).
- **ComfyUI version** — The node should target a clearly stated range of ComfyUI versions (or “latest stable”) and avoid relying on undocumented or internal APIs where possible, to reduce breakage on ComfyUI updates.

---

## Summary

| Area | Requirement |
|------|-------------|
| Install | Installable via ComfyUI Manager; no mandatory external setup at install time. |
| Config | Multiple LLM providers; all via OpenAI-compatible API; secrets in env/config, not in code. |
| Security | Read-only outside workspace; untrusted content from nodes sanitized; minimal read. |
| Usability | Multi-language responses; optional first-time onboarding. |
| Performance | Doc on demand; reasonable latency; context works without embeddings. |
| Compatibility | Stable tool/skill contracts; clear ComfyUI version target. |
