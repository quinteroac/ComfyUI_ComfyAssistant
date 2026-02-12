## Summary

Phase 8 adds **research tools** to the ComfyUI Assistant so the agent can search the web, fetch and extract content from URLs, and discover custom node packages from the ComfyUI Registry. This closes knowledge gaps when the LLM’s built-in knowledge is not enough.

## Changes

### Backend

- **`web_search.py`** — Web search: tries SearXNG (if `SEARXNG_URL` is set), then falls back to DuckDuckGo (`ddgs`).
- **`web_content.py`** — URL content extraction: tries Crawl4AI (optional), then aiohttp + BeautifulSoup. SSRF checks and ComfyUI workflow detection.
- **`node_registry.py`** — Client for the ComfyUI Registry API (`https://api.comfy.org/nodes`).

### API

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/research/search` | POST | Web search |
| `/api/research/fetch` | POST | Fetch URL content |
| `/api/research/registry` | GET | Search node registry |
| `/api/research/examples` | POST | Example workflows from ComfyUI_examples |

### Tools (agent-facing)

- **`webSearch`** — `query`, `maxResults`, `timeRange`
- **`fetchWebContent`** — `url`, `extractWorkflow`
- **`searchNodeRegistry`** — `query`, `limit`, `page`
- **`getExampleWorkflow`** — `category`, `query`, `maxResults`

### Frontend

- New tool definitions and implementations under `ui/src/tools/definitions/` and `ui/src/tools/implementations/` for the four tools above.
- `useComfyTools.ts` updated to register them.

### System prompt & docs

- **`system_context/skills/06_research_tools/SKILL.md`** — When and how to use research tools.
- **`system_context/01_role.md`** — Research capabilities and tools list.
- **`.env.example`** — Optional `SEARXNG_URL`.

### Dependencies

- **pyproject.toml**: `ddgs>=1.0.0`, `beautifulsoup4>=4.12.0`.
- Optional: `crawl4ai` for better extraction (fallback to bs4 if not installed).

## Design notes

- **Search**: SearXNG → DuckDuckGo.
- **Content**: Crawl4AI → aiohttp + BeautifulSoup.
- **SSRF**: `validate_url()` blocks `file://`, private IPs, localhost.
- **Limits**: 10K chars content, 5MB download.
- **Workflow detection**: Heuristic JSON scan for `class_type` + `inputs`.

## How to verify

1. `pip install ddgs beautifulsoup4` (and optionally `crawl4ai`).
2. Restart ComfyUI, build UI: `cd ui && npm run build`.
3. Try: “search for ComfyUI ControlNet tutorials”, “read this page: [URL]”, “find custom nodes for face detection”.
