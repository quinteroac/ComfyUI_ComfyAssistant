"""
Environment scanner for ComfyUI Assistant.

Scans the ComfyUI installation to discover installed node types,
custom node packages, and available models. Results are cached to
user_context/environment/*.json and a brief summary is injected
into the system prompt.

When searching nodes live, prefers ComfyUI's GET /object_info API
so the list matches what the server exposes (display_name, description, etc.).
"""

import json
import logging
import os
import sys
import traceback
from typing import Any

logger = logging.getLogger("ComfyUI_ComfyAssistant.env_scanner")


def _build_node_to_package_map() -> dict[str, str]:
    """Map each node type to its source custom_node package.

    Uses the class __module__ attribute to trace back to the package
    directory under custom_nodes/.
    """
    try:
        import nodes
    except ImportError:
        return {}

    mapping: dict[str, str] = {}
    for name, cls in getattr(nodes, "NODE_CLASS_MAPPINGS", {}).items():
        module = getattr(cls, "__module__", "") or ""
        parts = module.split(".")
        if len(parts) >= 2 and parts[0] == "custom_nodes":
            mapping[name] = parts[1]
        else:
            mapping[name] = "built-in"
    return mapping


def scan_installed_node_types() -> list[dict[str, Any]]:
    """Read nodes.NODE_CLASS_MAPPINGS and extract info per node type.

    Returns a list of dicts with keys: name, category, package,
    inputs (dict of input names/types), outputs (list of output type names).
    """
    try:
        import nodes
    except ImportError:
        logger.warning("Could not import nodes module")
        return []

    node_map = getattr(nodes, "NODE_CLASS_MAPPINGS", {})
    pkg_map = _build_node_to_package_map()
    result: list[dict[str, Any]] = []

    for name, cls in node_map.items():
        display_name = (
            getattr(cls, "NODE_DISPLAY_NAME", None)
            or getattr(cls, "DISPLAY_NAME", None)
            or ""
        )
        if isinstance(display_name, str):
            display_name = display_name.strip()
        else:
            display_name = ""
        doc = (getattr(cls, "__doc__") or "").strip()
        description = doc.split("\n")[0][:300].strip() if doc else ""

        entry: dict[str, Any] = {
            "name": name,
            "category": getattr(cls, "CATEGORY", "uncategorized"),
            "package": pkg_map.get(name, "unknown"),
            "display_name": display_name,
            "description": description,
        }

        # Extract input info
        inputs: dict[str, Any] = {}
        try:
            input_types = cls.INPUT_TYPES() if callable(getattr(cls, "INPUT_TYPES", None)) else {}
            for section in ("required", "optional"):
                section_data = input_types.get(section, {})
                for input_name, input_spec in section_data.items():
                    if isinstance(input_spec, (list, tuple)) and len(input_spec) > 0:
                        type_info = input_spec[0]
                        if isinstance(type_info, list):
                            inputs[input_name] = {"type": "COMBO", "options": type_info[:10], "section": section}
                        elif isinstance(type_info, str):
                            config = input_spec[1] if len(input_spec) > 1 and isinstance(input_spec[1], dict) else {}
                            inputs[input_name] = {"type": type_info, "section": section, **{k: v for k, v in config.items() if k in ("default", "min", "max", "step")}}
                        else:
                            inputs[input_name] = {"type": str(type_info), "section": section}
                    else:
                        inputs[input_name] = {"type": str(input_spec), "section": section}
        except Exception:
            pass

        entry["inputs"] = inputs

        # Extract output info
        output_types = getattr(cls, "RETURN_TYPES", ())
        output_names = getattr(cls, "RETURN_NAMES", ())
        outputs = []
        for i, otype in enumerate(output_types):
            oname = output_names[i] if i < len(output_names) else str(otype)
            outputs.append({"type": str(otype), "name": str(oname)})
        entry["outputs"] = outputs

        result.append(entry)

    return result


def _object_info_to_node_list(object_info: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert ComfyUI /object_info response to our node list format (name, category, package, display_name, description, inputs, outputs)."""
    pkg_map = _build_node_to_package_map()
    out: list[dict[str, Any]] = []
    for node_name, info in object_info.items():
        if not isinstance(info, dict):
            continue
        inp = info.get("input") or {}
        inputs_flat: dict[str, Any] = {}
        for section in ("required", "optional"):
            for k, v in (inp.get(section) or {}).items():
                if isinstance(v, (list, tuple)) and len(v) > 0:
                    typ = v[0]
                    if isinstance(typ, list):
                        inputs_flat[k] = {"type": "COMBO", "section": section}
                    else:
                        inputs_flat[k] = {"type": str(typ), "section": section}
                else:
                    inputs_flat[k] = {"type": str(v), "section": section}
        output_types = info.get("output") or []
        output_names = info.get("output_name") or output_types
        if isinstance(output_names, (list, tuple)):
            outputs = [
                {"type": str(t), "name": str(output_names[i]) if i < len(output_names) else str(t)}
                for i, t in enumerate(output_types)
            ]
        else:
            outputs = [{"type": str(t), "name": str(t)} for t in output_types]
        out.append({
            "name": node_name,
            "category": info.get("category") or "uncategorized",
            "package": pkg_map.get(node_name, "unknown"),
            "display_name": (info.get("display_name") or "") or node_name,
            "description": (info.get("description") or "").strip(),
            "inputs": inputs_flat,
            "outputs": outputs,
        })
    return out


def _get_comfyui_base_url() -> str | None:
    """Return base URL for the local ComfyUI server (e.g. http://127.0.0.1:8188), or None if unavailable."""
    try:
        import server
        ps = getattr(server, "PromptServer", None)
        if ps is None or not hasattr(ps, "instance"):
            return None
        instance = ps.instance
        port = getattr(instance, "port", None)
        address = getattr(instance, "address", "127.0.0.1")
        if port is None:
            return None
        return f"http://{address}:{port}"
    except Exception:
        return None


async def fetch_object_info_from_comfyui() -> list[dict[str, Any]] | None:
    """Fetch GET /object_info from the local ComfyUI server. Returns node list in our format, or None if unavailable."""
    base = _get_comfyui_base_url()
    if not base:
        return None

    try:
        import aiohttp
    except ImportError:
        return None

    url = f"{base}/object_info"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
    except Exception as e:
        logger.debug("fetch_object_info_from_comfyui: %s", e)
        return None

    if not isinstance(data, dict):
        return None
    logger.debug("fetch_object_info_from_comfyui: got %d nodes from API", len(data))
    return _object_info_to_node_list(data)


async def fetch_models_from_comfyui() -> dict[str, list[str]] | None:
    """Fetch GET /models and GET /models/{folder} from the local ComfyUI server.

    Returns dict mapping category name to list of filenames (same format as
    models.json cache), or None if unavailable.
    """
    base = _get_comfyui_base_url()
    if not base:
        return None

    try:
        import aiohttp
    except ImportError:
        return None

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base}/models") as resp:
                if resp.status != 200:
                    return None
                model_types = await resp.json()
            if not isinstance(model_types, list):
                return None
            result: dict[str, list[str]] = {}
            for folder in model_types:
                if not isinstance(folder, str):
                    continue
                async with session.get(f"{base}/models/{folder}") as resp:
                    if resp.status != 200:
                        result[folder] = []
                        continue
                    files = await resp.json()
                result[folder] = list(files) if isinstance(files, list) else []
            logger.debug("fetch_models_from_comfyui: got %d categories from API", len(result))
            return result
    except Exception as e:
        logger.debug("fetch_models_from_comfyui: %s", e)
        return None


def scan_custom_node_packages(custom_nodes_dir: str | None = None) -> list[dict[str, Any]]:
    """Walk custom_nodes/ directory, read pyproject.toml metadata if present.

    Returns list of dicts: name, path, has_agents, has_readme,
    description (from pyproject.toml if available).
    """
    if custom_nodes_dir is None:
        # Derive from this file's location: we're in custom_nodes/<package>/
        custom_nodes_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if not os.path.isdir(custom_nodes_dir):
        return []

    packages: list[dict[str, Any]] = []
    for entry_name in sorted(os.listdir(custom_nodes_dir)):
        entry_path = os.path.join(custom_nodes_dir, entry_name)
        if not os.path.isdir(entry_path):
            continue
        # Skip hidden dirs and __pycache__
        if entry_name.startswith(".") or entry_name == "__pycache__":
            continue

        pkg: dict[str, Any] = {
            "name": entry_name,
            "path": entry_path,
            "has_agents": os.path.isdir(os.path.join(entry_path, ".agents")),
            "has_readme": os.path.isfile(os.path.join(entry_path, "README.md")),
        }

        # Try reading description from pyproject.toml
        pyproject_path = os.path.join(entry_path, "pyproject.toml")
        if os.path.isfile(pyproject_path):
            try:
                if sys.version_info >= (3, 11):
                    import tomllib
                else:
                    try:
                        import tomllib
                    except ImportError:
                        import tomli as tomllib  # type: ignore[no-redef]
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                project = data.get("project", {})
                pkg["description"] = project.get("description", "")
                pkg["version"] = project.get("version", "")
            except Exception:
                pass

        packages.append(pkg)

    return packages


def scan_installed_models() -> dict[str, list[str]]:
    """Use folder_paths to list models by category.

    Returns dict mapping category name to list of filenames.
    """
    try:
        import folder_paths
    except ImportError:
        logger.warning("Could not import folder_paths module")
        return {}

    categories: dict[str, list[str]] = {}
    for category in ("checkpoints", "loras", "vae", "controlnet", "embeddings",
                      "upscale_models", "hypernetworks", "clip", "unet", "diffusion_models"):
        try:
            files = folder_paths.get_filename_list(category)
            categories[category] = list(files)
        except Exception:
            categories[category] = []

    return categories


def scan_environment(output_dir: str) -> dict[str, Any]:
    """Full environment scan; writes results to output_dir/*.json.

    Args:
        output_dir: Directory to write cached JSON files (user_context/environment/).

    Returns:
        Summary dict with counts.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Scan node types
    node_types = scan_installed_node_types()
    with open(os.path.join(output_dir, "installed_nodes.json"), "w", encoding="utf-8") as f:
        json.dump(node_types, f, indent=2, default=str)

    # Scan custom node packages
    packages = scan_custom_node_packages()
    # Serialize without full paths for security
    packages_clean = []
    for p in packages:
        packages_clean.append({
            "name": p["name"],
            "has_agents": p.get("has_agents", False),
            "has_readme": p.get("has_readme", False),
            "description": p.get("description", ""),
            "version": p.get("version", ""),
        })
    with open(os.path.join(output_dir, "custom_nodes.json"), "w", encoding="utf-8") as f:
        json.dump(packages_clean, f, indent=2)

    # Scan models
    models = scan_installed_models()
    with open(os.path.join(output_dir, "models.json"), "w", encoding="utf-8") as f:
        json.dump(models, f, indent=2)

    # Build summary
    total_models = sum(len(v) for v in models.values())
    # Count unique packages (excluding built-in)
    unique_packages = set()
    for n in node_types:
        pkg = n.get("package", "")
        if pkg and pkg != "built-in":
            unique_packages.add(pkg)

    # Count categories
    categories = set()
    for n in node_types:
        cat = n.get("category", "")
        if cat:
            categories.add(cat)

    summary = {
        "node_types_count": len(node_types),
        "custom_packages_count": len(unique_packages),
        "total_packages_count": len(packages),
        "models_count": total_models,
        "model_categories": {k: len(v) for k, v in models.items() if v},
        "node_categories_count": len(categories),
    }

    with open(os.path.join(output_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info(
        "Environment scan complete: %d node types, %d packages, %d models",
        summary["node_types_count"],
        summary["custom_packages_count"],
        summary["models_count"],
    )

    return summary


def get_cached_environment(env_dir: str) -> dict[str, Any] | None:
    """Read cached environment JSON files if they exist.

    Returns dict with keys: nodes, packages, models, summary.
    Returns None if cache doesn't exist.
    """
    summary_path = os.path.join(env_dir, "summary.json")
    if not os.path.isfile(summary_path):
        return None

    result: dict[str, Any] = {}
    for key, filename in [("nodes", "installed_nodes.json"),
                           ("packages", "custom_nodes.json"),
                           ("models", "models.json"),
                           ("summary", "summary.json")]:
        path = os.path.join(env_dir, filename)
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    result[key] = json.load(f)
            except (json.JSONDecodeError, OSError):
                result[key] = None
        else:
            result[key] = None

    return result


def get_environment_summary(env_dir: str) -> str:
    """Return a brief text summary for system prompt injection.

    Example: "87 custom node packages, 523 node types, 150 models.
    Use searchInstalledNodes/readDocumentation for details."
    """
    summary_path = os.path.join(env_dir, "summary.json")
    if not os.path.isfile(summary_path):
        return ""

    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
    except (json.JSONDecodeError, OSError):
        return ""

    node_count = summary.get("node_types_count", 0)
    pkg_count = summary.get("custom_packages_count", 0)
    model_count = summary.get("models_count", 0)

    model_detail = ""
    model_cats = summary.get("model_categories", {})
    if model_cats:
        parts = [f"{count} {cat}" for cat, count in sorted(model_cats.items()) if count > 0]
        if parts:
            model_detail = f" ({', '.join(parts)})"

    return (
        f"{pkg_count} custom node packages, {node_count} node types, "
        f"{model_count} models{model_detail}. "
        f"Use searchInstalledNodes/readDocumentation for details."
    )


def _filter_nodes(
    all_nodes: list[dict[str, Any]],
    query: str,
    category: str,
    limit: int,
) -> list[dict[str, Any]]:
    """Apply query/category/limit to a list of node dicts. Same logic for cache or live."""
    query_lower = query.lower().strip()
    category_lower = category.lower().strip()
    results: list[dict[str, Any]] = []
    for node in all_nodes:
        if category_lower:
            node_cat = (node.get("category") or "").lower()
            if category_lower not in node_cat:
                continue
        if query_lower:
            name = (node.get("name") or "").lower()
            cat = (node.get("category") or "").lower()
            pkg = (node.get("package") or "").lower()
            display_name = (node.get("display_name") or "").lower()
            description = (node.get("description") or "").lower()
            input_types = " ".join(
                str(v.get("type", "")) for v in (node.get("inputs") or {}).values()
            ).lower()
            # Match if query appears in any of these (substring, case-insensitive)
            if not (
                query_lower in name
                or query_lower in cat
                or query_lower in pkg
                or query_lower in display_name
                or query_lower in description
                or query_lower in input_types
            ):
                continue
        results.append(node)
        if len(results) >= limit:
            break
    return results


def search_nodes(
    env_dir: str,
    query: str = "",
    category: str = "",
    limit: int = 20,
    live_nodes_override: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Search installed node types: cache first, then live fallback if no results.

    Args:
        env_dir: Path to environment cache directory.
        query: Search string to match against node name, category, or package.
        category: Filter by category (case-insensitive substring match).
        limit: Maximum number of results.
        live_nodes_override: If provided, use this list for live fallback instead of
            scanning nodes locally. Typically from ComfyUI GET /object_info API.

    Returns:
        List of matching node type dicts. If cache has no matches and query is
        non-empty, uses live_nodes_override if provided, else scan_installed_node_types().
    """
    all_nodes: list[dict[str, Any]] = []
    nodes_path = os.path.join(env_dir, "installed_nodes.json")
    if os.path.isfile(nodes_path):
        try:
            with open(nodes_path, "r", encoding="utf-8") as f:
                all_nodes = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.debug("search_nodes: failed to read cache %s: %s", nodes_path, e)

    logger.debug(
        "search_nodes: query=%r category=%r limit=%s total_cached=%d",
        query, category, limit, len(all_nodes),
    )
    results = _filter_nodes(all_nodes, query, category, limit)

    if len(results) == 0 and query.strip():
        if live_nodes_override is not None:
            live_nodes = live_nodes_override
            logger.debug("search_nodes: 0 from cache, using ComfyUI API list (%d nodes)", len(live_nodes))
        else:
            live_nodes = scan_installed_node_types()
            logger.debug("search_nodes: 0 from cache, fallback to live scan (%d nodes)", len(live_nodes))
        results = _filter_nodes(live_nodes, query, category, limit)

    logger.debug("search_nodes: returning %d matches", len(results))
    return results
