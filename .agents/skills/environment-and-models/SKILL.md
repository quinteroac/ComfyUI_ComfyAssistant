---
name: environment-and-models
description: Environment scanning, caching, and model discovery for installed nodes, packages, and models
version: 0.0.1
license: MIT
---

# Environment and Models

The assistant knows what nodes and models are installed by scanning the ComfyUI environment and caching the results. This skill covers how scanning works, where caches live, and how the data is surfaced.

## `environment_scanner.py` Key Functions

| Function | Purpose |
|----------|---------|
| `scan_environment(output_dir)` | Full scan: nodes, packages, models. Writes JSON caches, returns summary dict |
| `scan_installed_node_types()` | Reads `nodes.NODE_CLASS_MAPPINGS` for all registered node types |
| `scan_custom_node_packages(custom_nodes_dir)` | Walks `custom_nodes/` for package metadata (pyproject.toml) |
| `scan_installed_models()` | Uses `folder_paths` to list models by category |
| `search_nodes(env_dir, query, category, limit)` | Search cached nodes; live API fallback if no results |
| `fetch_object_info_from_comfyui()` | Async GET `/object_info` from ComfyUI's local server |
| `fetch_models_from_comfyui()` | Async GET `/models` and `/models/{folder}` |
| `get_cached_environment(env_dir)` | Read all cached JSONs, return dict |
| `get_environment_summary(env_dir)` | Brief text summary from `summary.json` |

## Cache Files

Stored in `user_context/environment/`:

| File | Content |
|------|---------|
| `installed_nodes.json` | All node types with name, category, package, display_name, description, inputs, outputs |
| `custom_nodes.json` | Custom node packages with name, path, has_agents, has_readme, description, version |
| `models.json` | Dict of category -> list of filenames |
| `summary.json` | Brief counts (packages, node types, models) |

Model categories: `checkpoints`, `loras`, `vae`, `controlnet`, `embeddings`, `upscale_models`, `hypernetworks`, `clip`, `unet`, `diffusion_models`.

## Cache-First Strategy

1. **Search**: `search_nodes()` checks cached `installed_nodes.json` first
2. **Fallback**: If cache returns no results, calls `fetch_object_info_from_comfyui()` (live ComfyUI API)
3. **Filter**: Substring match on name, category, package, display_name, description, input_types
4. **Limit**: Returns up to `limit` results (default 20)

Models follow the same pattern: cache first, live API fallback via `fetch_models_from_comfyui()`.

## Auto-Scan on Startup

In `__init__.py`, `_auto_scan_environment()` runs as a background task 5 seconds after ComfyUI starts:
- Calls `scan_environment()` to populate all cache files
- Logs summary to console
- Subsequent requests use cached data for fast responses

## Related Tools and API Endpoints

| Tool / Endpoint | Purpose |
|-----------------|---------|
| `refreshEnvironment` tool | LLM-triggered rescan of nodes, packages, models |
| `searchInstalledNodes` tool | LLM searches installed node types |
| `getAvailableModels` tool | LLM lists models by category |
| `readDocumentation` tool | LLM fetches docs for a node type or topic |
| POST `/api/environment/scan` | HTTP trigger for full scan |
| GET `/api/environment/summary` | Brief text for prompt injection |
| GET `/api/environment/nodes` | Search nodes (`?q=&category=&limit=`) |
| GET `/api/environment/models` | List models (`?category=`) |
| GET `/api/environment/packages` | List custom node packages |
| GET `/api/environment/docs` | Fetch docs (`?topic=&source=`) |

## FAQ

### How does the assistant know which nodes and models are available?
On startup, `_auto_scan_environment()` scans everything and caches to `user_context/environment/`. The summary is injected into the system prompt via `load_environment_summary()`. Tools like `searchInstalledNodes` and `getAvailableModels` query the cache (with live fallback).

### Where do I change or extend what gets scanned?
Edit `environment_scanner.py`. The three scan functions (`scan_installed_node_types`, `scan_custom_node_packages`, `scan_installed_models`) each write their own JSON cache. Add new scan functions and register them in `scan_environment()`.

### How do I add a new model category?
Add the folder name to the categories list in `scan_installed_models()` in `environment_scanner.py`. The category maps to ComfyUI's `folder_paths` system.

### How do I force a rescan?
Either: (1) the LLM calls the `refreshEnvironment` tool, (2) POST `/api/environment/scan`, or (3) restart ComfyUI (auto-scan runs after 5s).

## Related Skills

- `system-and-user-context` -- how environment summary is injected into the system prompt
- `backend-architecture` -- API endpoints for environment queries
- `backend-tools-declaration` -- environment tool definitions
