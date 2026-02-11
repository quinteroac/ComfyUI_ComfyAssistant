"""
ComfyUI_examples local reference loader.

Provides access to workflows extracted from the ComfyUI_examples repository.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
REFERENCES_DIR = (
    BASE_DIR
    / "system_context"
    / "skills"
    / "08_comfyui_examples_source"
    / "references"
)


@lru_cache(maxsize=1)
def _load_index() -> Dict[str, Any]:
    index_path = REFERENCES_DIR / "comfyui_examples_index.json"
    if not index_path.exists():
        return {"categories": {}}
    return json.loads(index_path.read_text(encoding="utf-8"))


@lru_cache(maxsize=32)
def _load_category(category: str) -> Dict[str, Any]:
    file_path = REFERENCES_DIR / f"comfyui_examples_{category}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Unknown category: {category}")
    return json.loads(file_path.read_text(encoding="utf-8"))


def list_categories() -> List[str]:
    index = _load_index()
    return sorted(index.get("categories", {}).keys())


def get_examples(
    category: str,
    query: Optional[str] = None,
    max_results: int = 5,
) -> Dict[str, Any]:
    data = _load_category(category)
    entries = data.get("entries", [])

    q = (query or "").strip().lower()
    if q:
        filtered = []
        for entry in entries:
            haystacks = [
                entry.get("image", ""),
                entry.get("file", ""),
            ]
            if any(q in str(h).lower() for h in haystacks):
                filtered.append(entry)
        entries = filtered

    max_results = max(1, min(20, max_results))
    results: List[Dict[str, Any]] = []

    def _extract_display_names(graph: Dict[str, Any]) -> Dict[str, str]:
        display_names: Dict[str, str] = {}
        for node in graph.get("nodes", []):
            if not isinstance(node, dict):
                continue
            node_id = node.get("id")
            title = node.get("title")
            if node_id is not None and title:
                display_names[str(node_id)] = title
        return display_names

    def _extract_title_type_map(graph: Dict[str, Any]) -> Dict[str, str]:
        title_map: Dict[str, str] = {}
        for node in graph.get("nodes", []):
            if not isinstance(node, dict):
                continue
            title = node.get("title")
            node_type = node.get("type")
            if title and node_type:
                title_map[title] = node_type
        return title_map

    def _is_graph_format(data: Any) -> bool:
        return isinstance(data, dict) and isinstance(data.get("nodes"), list)

    for entry in entries[:max_results]:
        prompt = entry.get("prompt")
        workflow_graph = entry.get("workflow")
        workflow_api = None
        workflow_format = "unknown"
        display_names: Dict[str, str] = {}

        if _is_graph_format(prompt):
            workflow_graph = prompt
            workflow_format = "graph"
        elif isinstance(prompt, dict):
            workflow_api = prompt
            workflow_format = "api"

        if _is_graph_format(workflow_graph):
            display_names = _extract_display_names(workflow_graph)
            title_type_map = _extract_title_type_map(workflow_graph)

        if not workflow_api and not workflow_graph:
            continue
        result = {
            "source": entry.get("source"),
            "workflow": workflow_api,
            "workflowFormat": workflow_format,
            "displayNames": display_names,
            "titleTypeMap": title_type_map if _is_graph_format(workflow_graph) else {},
        }
        if entry.get("image"):
            result["image"] = entry.get("image")
        if entry.get("file"):
            result["file"] = entry.get("file")
        if workflow_api is None and workflow_graph is not None:
            result["workflowGraph"] = workflow_graph
        results.append(result)

    return {
        "category": category,
        "query": query or "",
        "count": len(results),
        "results": results,
    }
