"""
ComfyUI Registry API client.

Searches the ComfyUI Registry (https://api.comfy.org/nodes) for custom
node packages by name, description, or tags.
"""

import logging
from typing import Any, Dict

import aiohttp

logger = logging.getLogger("ComfyUI_ComfyAssistant.node_registry")

REGISTRY_API_BASE = "https://api.comfy.org"


async def search_node_registry(
    query: str,
    limit: int = 10,
    page: int = 1,
) -> Dict[str, Any]:
    """Search the ComfyUI Registry for custom node packages.

    Args:
        query: Search term (name, description, tags).
        limit: Maximum results per page (1-50, default 10).
        page: Page number (default 1).

    Returns:
        Dict with keys: nodes (list of package info dicts),
        total (int), page (int), totalPages (int).

    Raises:
        RuntimeError: If the API request fails.
    """
    limit = max(1, min(50, limit))
    page = max(1, page)

    params = {
        "search": query,
        "limit": str(limit),
        "page": str(page),
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{REGISTRY_API_BASE}/nodes",
                params=params,
                timeout=aiohttp.ClientTimeout(total=10),
                headers={"Accept": "application/json"},
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
    except aiohttp.ClientError as e:
        raise RuntimeError(f"ComfyUI Registry API request failed: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error querying registry: {e}") from e

    # Normalize response — the registry API may use varying field names
    raw_nodes = data.get("nodes", data.get("results", []))
    total = data.get("total", data.get("totalCount", len(raw_nodes)))
    total_pages = data.get("totalPages", data.get("total_pages", 1))

    nodes = []
    for item in raw_nodes:
        nodes.append({
            "id": item.get("id", ""),
            "name": item.get("name", item.get("display_name", "")),
            "author": item.get("author", item.get("publisher", {}).get("name", "")),
            "description": item.get("description", ""),
            "downloads": item.get("downloads", item.get("download_count", 0)),
            "repository": item.get("repository", item.get("repo_url", "")),
            "tags": item.get("tags", []),
        })

    return {
        "nodes": nodes,
        "total": total,
        "page": page,
        "totalPages": total_pages,
    }
