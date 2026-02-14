# Phase 6 — Risk mitigation (post–Phase 3 review)

**Status**: Planned

**Goal:** Address risks identified in the Phase 3 PR review (Bugbot — Medium Risk): new backend APIs, background scanning, prompt injection, and the `@assistant-ui/react-ai-sdk` patch. Document and, where applicable, implement mitigations.

---

## Observations to address (Bugbot — Medium Risk)

### 1. New backend APIs

**Risk:** New endpoints in `api_handlers.py` (environment scan/search/models/packages/docs, skill CRUD) increase attack surface and must follow the same access policy as the rest of the backend.

**Mitigations:**

- [ ] Confirm all Phase 3 endpoints are served by the same ComfyUI/extension process and are not exposed beyond the existing server (e.g. local/sidebar only).
- [ ] Document in `api_handlers.py` or in an architecture doc the list of routes and assumptions (e.g. "same origin", "no public internet exposure").
- [ ] No new secrets or unauthenticated public endpoints.

**References:** `api_handlers.py`, `register_routes()` in same file.

---

### 2. Background scanning

**Risk:** Auto-scan on startup (with delay) touches disk and possibly ComfyUI; if it fails or is heavy, it could affect startup or resource usage.

**Mitigations:**

- [ ] Ensure scan failure does not block startup (already non-blocking with delay; verify error handling).
- [ ] Consider making auto-scan explicitly optional via configuration (e.g. env or settings).
- [ ] Define or enforce limits: max scan duration, max cache size or summary length, to avoid unbounded growth.

**References:** `__init__.py` (schedule of initial scan), `environment_scanner.py`, `user_context/environment/`.

---

### 3. Prompt injection (environment summary)

**Risk:** Injecting the environment summary into the system prompt means "what the model sees" depends on generated data. If the summary were malformed or attacker-controlled, it could influence model behaviour.

**Mitigations:**

- [ ] Document that the injected summary comes from **our controlled cache** (not raw user input).
- [ ] Keep or define a **strict size limit** for the injected summary (e.g. in `user_context_loader.get_environment_summary()` / `environment_scanner.get_environment_summary()`).
- [ ] Add a short note in Phase 5/6 docs: "The model receives a bounded, internally generated summary; we do not inject arbitrary user content here."

**References:** `agent_prompts.py`, `user_context_loader.py`, `environment_scanner.get_environment_summary()`, `summary.json`.

---

### 4. Patch to `@assistant-ui/react-ai-sdk`

**Risk:** Patching tool-call execution in the chat runtime can affect all tool behaviour. If the patch is wrong, tool calls might not run or results might not be sent back correctly.

**Mitigations:**

- [ ] Document the patch in `ui/patches/`: what problem it fixes (execute streamed tool calls and return results) and what it does **not** change (tool semantics).
- [ ] When upgrading `@assistant-ui/react-ai-sdk`, re-apply or re-evaluate the patch and add a smoke test: "tool call → execution → result visible in chat."

**References:** `ui/patches/@assistant-ui+react-ai-sdk+1.3.6.patch`, `useComfyTools.ts`, tool implementations.

---

## Deliverables

| Item | Description | Status |
|------|-------------|--------|
| Risks doc | This file: observations + checklist | Done |
| Phase 6 in planning | `planning/comfyui_assistant_development_phases.md` — Phase 6 section | Done |
| API/docs review | Apply checklist items above (document routes, summary limit, patch doc) | Pending |
| Optional config | Auto-scan toggle or env flag | Optional |
| Patch upgrade plan | Note in README or .agents/ for assistant-ui upgrades | Pending |

---

## Success criteria

- All four risk areas documented with mitigations (done or accepted).
- At least: route assumptions documented; environment summary size bounded and documented; patch purpose documented.
- No regression in Phase 3 behaviour after any code changes.
