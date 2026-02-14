# Phase 8 — Research and Self-Service

## Overview

Phase 8 adds research tools to the ComfyUI Assistant, enabling the agent to search the web, fetch and extract content from URLs, and discover custom node packages from the ComfyUI Registry. This bridges knowledge gaps when the LLM's built-in knowledge is insufficient.

## Deliverables

### New backend modules

| File | Purpose |
|------|---------|
| `web_search.py` | Web search provider abstraction. Tries SearXNG (if `SEARXNG_URL` is set) then falls back to DuckDuckGo (`ddgs` package). |
| `web_content.py` | Content extraction from URLs. Tries Crawl4AI (optional) then falls back to aiohttp + BeautifulSoup. Includes SSRF prevention and ComfyUI workflow detection. |
| `node_registry.py` | ComfyUI Registry API client. Searches `https://api.comfy.org/nodes` for custom node packages. |

### New API endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/research/search` | POST | Web search (body: `{query, maxResults?, timeRange?}`) |
| `/api/research/fetch` | POST | Fetch URL content (body: `{url, extractWorkflow?}`) |
| `/api/research/registry` | GET | Search node registry (`?q=...&limit=...&page=...`) |
| `/api/research/examples` | POST | Fetch example workflows (body: `{category, query?, maxResults?}`) |

### New tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `webSearch` | `query` (required), `maxResults`, `timeRange` | Search the web for ComfyUI resources |
| `fetchWebContent` | `url` (required), `extractWorkflow` | Fetch and extract content from a URL |
| `searchNodeRegistry` | `query` (required), `limit`, `page` | Search the ComfyUI Registry for custom node packages |
| `getExampleWorkflow` | `category` (required), `query`, `maxResults` | Fetch extracted workflows from ComfyUI_examples |

### Frontend files

- `ui/src/tools/definitions/web-search.ts` — Zod schema + definition
- `ui/src/tools/definitions/fetch-web-content.ts` — Zod schema + definition
- `ui/src/tools/definitions/search-node-registry.ts` — Zod schema + definition
- `ui/src/tools/definitions/get-example-workflow.ts` — Zod schema + definition
- `ui/src/tools/implementations/web-search.ts` — POST `/api/research/search`
- `ui/src/tools/implementations/fetch-web-content.ts` — POST `/api/research/fetch`
- `ui/src/tools/implementations/search-node-registry.ts` — GET `/api/research/registry`
- `ui/src/tools/implementations/get-example-workflow.ts` — POST `/api/research/examples`

### System prompt

- `system_context/skills/06_research_tools/SKILL.md` — LLM guidance for when and how to use research tools, research-to-skill flow

### Modified files

| File | Change |
|------|--------|
| `api_handlers.py` | Added `create_research_handlers()` and `register_research_routes()` |
| `__init__.py` | Registered Phase 8 routes (2 lines) |
| `tools_definitions.py` | Added 4 tool declarations (webSearch, fetchWebContent, searchNodeRegistry, getExampleWorkflow) |
| `comfyui_examples.py` | Load extracted ComfyUI_examples workflows (Phase 8) |
| `ui/src/tools/definitions/index.ts` | Added 4 barrel exports |
| `ui/src/tools/implementations/index.ts` | Added 4 barrel exports |
| `ui/src/hooks/useComfyTools.ts` | Added 4 `useAssistantTool()` calls |
| `system_context/01_role.md` | Added research capabilities to role description and tools list |
| `pyproject.toml` | Added `ddgs>=1.0.0` and `beautifulsoup4>=4.12.0` |
| `.env.example` | Added `SEARXNG_URL` (optional) |

## Dependencies

### Required (added to pyproject.toml)

- `ddgs>=1.0.0` — Free web search fallback
- `beautifulsoup4>=4.12.0` — HTML content extraction

### Optional (not in pyproject.toml — heavy dependency)

- `crawl4ai` — Better content extraction via Playwright. Imported with try/except; falls back to bs4 when not installed.

## Architecture decisions

- **Search fallback chain**: SearXNG (self-hosted, configurable) → DuckDuckGo (free, no API key)
- **Content extraction fallback**: Crawl4AI (JS-rendered pages) → aiohttp + BeautifulSoup (lightweight)
- **SSRF prevention**: `validate_url()` blocks `file://`, private IPs, localhost, reserved ranges
- **Content limits**: 10K chars max content, 5MB max download size
- **Workflow detection**: Heuristic JSON scanning for objects with `class_type` + `inputs` keys
- **Registry normalization**: Handles varying field names from the ComfyUI Registry API

## Verification

1. Install deps: `pip install ddgs beautifulsoup4`
2. Restart ComfyUI
3. Build frontend: `cd ui && npm run build`
4. Test webSearch: Ask "search for ComfyUI ControlNet tutorials"
5. Test fetchWebContent: Ask "read this page: [URL]"
6. Test searchNodeRegistry: Ask "find custom nodes for face detection"
7. Test fallbacks: Unset SEARXNG_URL → DDG should be used
