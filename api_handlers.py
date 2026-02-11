"""
API endpoint handlers for environment, documentation, skill management,
and research tools.

Extracted from __init__.py for maintainability. All handlers are async
aiohttp request handlers that return web.Response.
"""

import json
import logging

from aiohttp import web

import environment_scanner
import documentation_resolver
import skill_manager
import user_context_store
import comfyui_examples
import web_search
import web_content
import node_registry

logger = logging.getLogger("ComfyUI_ComfyAssistant.api")


def create_handlers(environment_dir: str, system_context_path: str) -> dict:
    """Create handler functions with bound configuration paths.

    Args:
        environment_dir: Path to user_context/environment/ cache directory.
        system_context_path: Path to system_context/ directory.

    Returns:
        Dict mapping handler names to async handler functions.
    """

    async def environment_scan_handler(request: web.Request) -> web.Response:
        """POST /api/environment/scan — trigger full environment scan."""
        try:
            user_context_store.ensure_environment_dirs()
            summary = environment_scanner.scan_environment(environment_dir)
            return web.json_response({"ok": True, "summary": summary})
        except Exception as e:
            logger.error("Environment scan failed: %s", e, exc_info=True)
            return web.json_response({"error": str(e)}, status=500)

    async def environment_summary_handler(request: web.Request) -> web.Response:
        """GET /api/environment/summary — brief summary for prompt injection."""
        try:
            summary = environment_scanner.get_environment_summary(environment_dir)
            return web.json_response({"summary": summary})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def environment_nodes_handler(request: web.Request) -> web.Response:
        """GET /api/environment/nodes — search installed node types."""
        query = request.query.get("q", "")
        category = request.query.get("category", "")
        try:
            limit = int(request.query.get("limit", "20"))
        except ValueError:
            limit = 20
        # Always visible in console (logger may be filtered)
        print(f"[ComfyAssistant] GET /api/environment/nodes q={query!r} category={category!r} limit={limit}", flush=True)
        logger.info(
            "GET /api/environment/nodes q=%r category=%r limit=%s",
            query, category, limit,
        )
        logger.debug(
            "environment_nodes: env_dir=%s",
            environment_dir,
        )
        try:
            live_nodes = await environment_scanner.fetch_object_info_from_comfyui()
            results = environment_scanner.search_nodes(
                environment_dir,
                query=query,
                category=category,
                limit=limit,
                live_nodes_override=live_nodes,
            )
            print(f"[ComfyAssistant] environment_nodes: {len(results)} results for q={query!r}", flush=True)
            logger.info("environment_nodes: %d results for q=%r", len(results), query)
            logger.debug("environment_nodes: found %d results", len(results))
            return web.json_response({"nodes": results, "count": len(results)})
        except Exception as e:
            logger.exception("environment_nodes failed")
            return web.json_response({"error": str(e)}, status=500)

    async def environment_models_handler(request: web.Request) -> web.Response:
        """GET /api/environment/models — list models by category. Cache first, then ComfyUI API fallback.
        Optional query param: category (e.g. checkpoints, loras) to return only that category."""
        try:
            cached = environment_scanner.get_cached_environment(environment_dir)
            models = cached.get("models", {}) if cached else {}
            if not models:
                models = await environment_scanner.fetch_models_from_comfyui() or {}
            category = (request.query.get("category") or "").strip()
            if category and isinstance(models, dict):
                models = {category: models.get(category, [])}
            return web.json_response({"models": models})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def environment_packages_handler(request: web.Request) -> web.Response:
        """GET /api/environment/packages — list custom node packages."""
        try:
            cached = environment_scanner.get_cached_environment(environment_dir)
            packages = cached.get("packages", []) if cached else []
            return web.json_response({"packages": packages})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def environment_docs_handler(request: web.Request) -> web.Response:
        """GET /api/environment/docs — fetch documentation for a topic."""
        topic = request.query.get("topic", "")
        if not topic:
            return web.json_response(
                {"error": "Missing 'topic' query parameter"}, status=400
            )
        source = request.query.get("source", "any")
        try:
            result = documentation_resolver.resolve_documentation(
                topic=topic,
                source=source,
                system_context_dir=system_context_path,
            )
            return web.json_response(result)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def skills_handler(request: web.Request) -> web.Response:
        """POST /api/user-context/skills — create skill.
        GET /api/user-context/skills — list skills."""
        if request.method == "POST":
            try:
                body = await request.json() if request.body_exists else {}
            except json.JSONDecodeError:
                return web.json_response({"error": "Invalid JSON body"}, status=400)
            try:
                result = skill_manager.create_skill(
                    name=body.get("name", ""),
                    description=body.get("description", ""),
                    instructions=body.get("instructions", ""),
                )
                return web.json_response({"ok": True, "skill": result})
            except ValueError as e:
                return web.json_response({"error": str(e)}, status=400)
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)
        else:
            # GET
            try:
                skills = skill_manager.list_skills()
                return web.json_response({"skills": skills})
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)

    async def skill_delete_handler(request: web.Request) -> web.Response:
        """DELETE /api/user-context/skills/{slug} — delete skill."""
        slug = request.match_info.get("slug", "")
        try:
            deleted = skill_manager.delete_skill(slug)
            if not deleted:
                return web.json_response(
                    {"error": f"Skill '{slug}' not found"}, status=404
                )
            return web.json_response({"ok": True, "slug": slug})
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def skill_update_handler(request: web.Request) -> web.Response:
        """PATCH /api/user-context/skills/{slug} — update skill."""
        slug = request.match_info.get("slug", "")
        try:
            body = await request.json() if request.body_exists else {}
        except json.JSONDecodeError:
            return web.json_response({"error": "Invalid JSON body"}, status=400)
        name = body.get("name") if "name" in body else None
        description = body.get("description") if "description" in body else None
        instructions = body.get("instructions") if "instructions" in body else None
        if name is None and description is None and instructions is None:
            return web.json_response(
                {"error": "At least one of name, description, or instructions is required"},
                status=400,
            )
        try:
            result = skill_manager.update_skill(
                slug, name=name, description=description, instructions=instructions
            )
            return web.json_response({"ok": True, "skill": result})
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    return {
        "environment_scan": environment_scan_handler,
        "environment_summary": environment_summary_handler,
        "environment_nodes": environment_nodes_handler,
        "environment_models": environment_models_handler,
        "environment_packages": environment_packages_handler,
        "environment_docs": environment_docs_handler,
        "skills": skills_handler,
        "skill_delete": skill_delete_handler,
        "skill_update": skill_update_handler,
    }


def register_routes(app, handlers: dict) -> None:
    """Register all Phase 3 routes on the aiohttp app.

    Args:
        app: The aiohttp web application.
        handlers: Dict from create_handlers().
    """
    app.add_routes([
        web.post("/api/environment/scan", handlers["environment_scan"]),
        web.get("/api/environment/summary", handlers["environment_summary"]),
        web.get("/api/environment/nodes", handlers["environment_nodes"]),
        web.get("/api/environment/models", handlers["environment_models"]),
        web.get("/api/environment/packages", handlers["environment_packages"]),
        web.get("/api/environment/docs", handlers["environment_docs"]),
        web.post("/api/user-context/skills", handlers["skills"]),
        web.get("/api/user-context/skills", handlers["skills"]),
        web.delete("/api/user-context/skills/{slug}", handlers["skill_delete"]),
        web.patch("/api/user-context/skills/{slug}", handlers["skill_update"]),
    ])


# ---------------------------------------------------------------------------
# Phase 8 — Research handlers
# ---------------------------------------------------------------------------


def create_research_handlers() -> dict:
    """Create handler functions for research endpoints (Phase 8).

    Returns:
        Dict mapping handler names to async handler functions.
    """

    async def search_handler(request: web.Request) -> web.Response:
        """POST /api/research/search — web search."""
        try:
            body = await request.json() if request.body_exists else {}
        except json.JSONDecodeError:
            return web.json_response({"error": "Invalid JSON body"}, status=400)

        query = (body.get("query") or "").strip()
        if not query:
            return web.json_response(
                {"error": "Missing required field: query"}, status=400
            )

        max_results = body.get("maxResults", 5)
        time_range = body.get("timeRange")

        try:
            result = await web_search.web_search(
                query=query,
                max_results=max_results,
                time_range=time_range,
            )
            return web.json_response(result)
        except RuntimeError as e:
            logger.warning("Web search failed: %s", e)
            return web.json_response({"error": str(e)}, status=503)
        except Exception as e:
            logger.exception("Unexpected error in web search")
            return web.json_response({"error": str(e)}, status=500)

    async def fetch_handler(request: web.Request) -> web.Response:
        """POST /api/research/fetch — fetch and extract web content."""
        try:
            body = await request.json() if request.body_exists else {}
        except json.JSONDecodeError:
            return web.json_response({"error": "Invalid JSON body"}, status=400)

        url = (body.get("url") or "").strip()
        if not url:
            return web.json_response(
                {"error": "Missing required field: url"}, status=400
            )

        extract_workflow = body.get("extractWorkflow", True)

        try:
            result = await web_content.fetch_web_content(
                url=url,
                extract_workflow=extract_workflow,
            )
            return web.json_response(result)
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)
        except RuntimeError as e:
            logger.warning("Content fetch failed: %s", e)
            return web.json_response({"error": str(e)}, status=502)
        except Exception as e:
            logger.exception("Unexpected error in content fetch")
            return web.json_response({"error": str(e)}, status=500)

    async def registry_handler(request: web.Request) -> web.Response:
        """GET /api/research/registry — search ComfyUI Registry."""
        query = (request.query.get("q") or "").strip()
        if not query:
            return web.json_response(
                {"error": "Missing required query parameter: q"}, status=400
            )

        try:
            limit = int(request.query.get("limit", "10"))
        except ValueError:
            limit = 10

        try:
            page = int(request.query.get("page", "1"))
        except ValueError:
            page = 1

        try:
            result = await node_registry.search_node_registry(
                query=query,
                limit=limit,
                page=page,
            )
            return web.json_response(result)
        except RuntimeError as e:
            logger.warning("Registry search failed: %s", e)
            return web.json_response({"error": str(e)}, status=502)
        except Exception as e:
            logger.exception("Unexpected error in registry search")
            return web.json_response({"error": str(e)}, status=500)

    async def examples_handler(request: web.Request) -> web.Response:
        """POST /api/research/examples — get example workflows."""
        try:
            body = await request.json() if request.body_exists else {}
        except json.JSONDecodeError:
            return web.json_response({"error": "Invalid JSON body"}, status=400)

        category = (body.get("category") or "").strip()
        if not category:
            return web.json_response(
                {"error": "Missing required field: category"}, status=400
            )

        query = (body.get("query") or "").strip()
        max_results = body.get("maxResults", 5)

        try:
            result = comfyui_examples.get_examples(
                category=category,
                query=query or None,
                max_results=max_results,
            )
            return web.json_response(result)
        except FileNotFoundError as e:
            return web.json_response({"error": str(e)}, status=404)
        except Exception as e:
            logger.exception("Unexpected error in examples lookup")
            return web.json_response({"error": str(e)}, status=500)

    return {
        "search": search_handler,
        "fetch": fetch_handler,
        "registry": registry_handler,
        "examples": examples_handler,
    }


def register_research_routes(app, handlers: dict) -> None:
    """Register Phase 8 research routes on the aiohttp app.

    Args:
        app: The aiohttp web application.
        handlers: Dict from create_research_handlers().
    """
    app.add_routes([
        web.post("/api/research/search", handlers["search"]),
        web.post("/api/research/fetch", handlers["fetch"]),
        web.get("/api/research/registry", handlers["registry"]),
        web.post("/api/research/examples", handlers["examples"]),
    ])
