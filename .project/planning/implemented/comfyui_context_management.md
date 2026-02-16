# ComfyUI context management

This document describes the **actions the system performs to manage context efficiently**: how the system message is built, when full context is sent vs a short continuation, how history and tool results are trimmed, and which parts are loaded on demand to stay within token limits.

## Overview

Context is managed to:

- Avoid re-sending the same long system prompt on every request.
- Keep the conversation history and tool results within a bounded size.
- Load heavy content (user skills, model-specific system skills) **on demand** via tools instead of in the initial system message.

**Current approach:** The system today relies on **truncation** (hard character limits, drop older messages) to stay within context. Truncation is aggressive and can discard important information. A preferred direction is to move toward **summarization**: produce short summaries that retain only relevant content instead of cutting text or history blindly (see [Next steps](#10-next-steps-for-context-management)).

Main components:

| Component | Role |
|-----------|------|
| `user_context_loader.py` | Loads system context, user context, environment summary, and user skills (with size caps). |
| `agent_prompts.py` | Assembles the system message and formats user context with truncation. |
| `__init__.py` (chat handler) | Decides full vs continuation system message; trims tool results and history; applies env-tunable limits. |

---

## 1. System message: full vs continuation

**When:** On each `POST /api/chat`, the handler checks whether the request already has a system message and whether there is prior assistant content.

**Actions:**

1. **If there is no system message in the request:**
   - **If there is at least one prior assistant message** (continuation turn):  
     Insert a **short continuation** system message (`get_system_message_continuation()`).  
     Content: *"You are ComfyUI Assistant. Continue the conversation. Apply the same rules, tools, and user context as in the initial system message."*  
     → The full context was already sent on the first turn; no need to re-send it.
   - **If there is no prior assistant message** (first turn):  
     Load full context (see below), truncate system context if needed, then insert the **full** system message via `get_system_message(...)`.

2. **If there is already a system message** in the request:  
   Do not replace it; the client is re-sending a previously built system message.

**Result:** Full context is sent only once per thread (first user message); all later turns use the short continuation, reducing tokens on every subsequent request.

---

## 2. Loading pipeline (first turn only)

When building the **full** system message, the following is loaded in order:

| Step | Source | Function / logic |
|------|--------|-------------------|
| 1 | `system_context/` | `load_system_context(system_context_path)`: top-level `.md` files in sorted order, then `system_context/skills/*/SKILL.md` (excluding `model_*` folders). Concatenated into one string. |
| 2 | Truncation | `_truncate_chars(system_context_text, LLM_SYSTEM_CONTEXT_MAX_CHARS)` so system context does not exceed the env limit (default 12000 chars). |
| 3 | Fallback | If after truncation the system context is empty, a minimal default prompt is used (role + basic tools + language instruction). |
| 4 | User context | `load_user_context()`: rules from DB, `SOUL.md`, `goals.md`, preferences. **User skills are not loaded here**; they are on demand (see below). |
| 5 | Environment | `load_environment_summary()`: brief text from `user_context/environment/summary.json` (e.g. "87 packages, 523 node types, 150 models"). |
| 6 | Assembly | `get_system_message(system_context_text, user_context, environment_summary, user_context_max_chars=...)` builds the final system message: system context + instructions for on-demand user/model skills + environment block + formatted user context (rules, SOUL, goals). |

User context block is itself capped: `format_user_context()` applies `max_chars` (default 2500 via `LLM_USER_CONTEXT_MAX_CHARS`), `max_narrative_chars` (1200 for SOUL+goals), and `max_rules` (12). Text is hard-truncated with a `"... [truncated]"` suffix when over limits.

---

## 3. On-demand context (no injection in system message)

To keep the system message small and avoid loading rarely used content:

- **User skills:** Not embedded in the system message. The system message tells the model to use `listUserSkills` and `getUserSkill(slug)` when the user refers to a skill or when applying a remembered preference. Skills are loaded only when the model calls the tool.
- **Model-specific system skills:** Skills under `system_context/skills/` whose folder name contains `model_` (e.g. `09_model_flux`) are **not** included in `load_system_context()`. The system message instructs the model to call `listSystemSkills`, then `getSystemSkill(slug)` when the user asks about a model or workflow for that model. The backend serves these via `GET /api/system-context/skills` and `GET /api/system-context/skills/{slug}`.

This keeps the initial system message shorter and loads heavy skill text only when relevant.

---

## 4. Slash command `/skill <name>`

Before calling the LLM, the handler runs `_inject_skill_if_slash_skill(openai_messages)`:

- If the last user message is `/skill <name>` (or slug), the backend resolves the skill by name/slug and **replaces** that user message content with the skill’s instructions (plus a short note that the user activated that skill). The model thus receives the skill content as the user message for that turn, without putting it in the system message.

---

## 5. Trimming tool results

**When:** After system message handling and `/skill` injection, before sending messages to the LLM.

**Action:** `_trim_old_tool_results(messages, keep_last_n_rounds)`.

- A **round** is one assistant message that contains `tool_calls` plus the immediately following consecutive `tool` messages (the results for those calls).
- Only the last **N** rounds keep their full tool result content (N = `LLM_TOOL_RESULT_KEEP_LAST_ROUNDS`, default 2).
- Older tool messages get their `content` replaced with a short JSON placeholder:  
  `{"_omitted": true, "note": "Earlier tool result omitted to save context"}`.

**Result:** The order of messages is preserved (so tool_call/tool_result pairing stays valid), but the payload size is reduced by omitting large tool outputs from earlier rounds.

---

## 6. Trimming conversation history

**When:** After trimming tool results, before sending to the LLM.

**Action:** `_trim_openai_history(messages, max_non_system_messages)`.

- All **system** messages are kept.
- **Non-system** messages (user, assistant, tool) are trimmed to the last `max_non_system_messages` (default: `LLM_HISTORY_MAX_MESSAGES` = 24).
- If the trimmed tail starts with a `tool` message (orphan result), that leading tool message is dropped so the history does not start mid-round.

**Result:** The request only sends a bounded tail of the conversation, preventing unbounded growth of history tokens.

---

## 7. Order of operations in the chat handler

For each `POST /api/chat`, the sequence is:

1. Parse body and convert UI messages to OpenAI format (`_ui_messages_to_openai`).
2. If no system message:
   - If there is prior assistant content → insert **continuation** system message.
   - Else → load system context, user context, environment summary; truncate system context; build and insert **full** system message.
3. Run **`_inject_skill_if_slash_skill`** (replace last user message with skill instructions when the user typed `/skill <name>`).
4. **Trim old tool results** (`_trim_old_tool_results` with `LLM_TOOL_RESULT_KEEP_LAST_ROUNDS`).
5. **Trim history** (`_trim_openai_history` with `LLM_HISTORY_MAX_MESSAGES`).
6. Proceed to LLM call with the resulting message list.

---

## 8. Token/size budget constants

| Location | Constant / env | Default | Purpose |
|----------|----------------|---------|---------|
| `user_context_loader.py` | `MAX_USER_CONTEXT_CHARS` | 4000 | Loader-level reference for user context block size. |
| `user_context_loader.py` | `MAX_SKILLS_FULL_CHARS` | 1500 | If total user skills text ≤ this, include full skill text when skills were injected; else use summaries. (User skills are now on demand; this applies to any path that still aggregates skills.) |
| `user_context_loader.py` | `MAX_NARRATIVE_CHARS` | 1200 | Max combined length for SOUL + goals in narrative block. |
| `agent_prompts.py` | `DEFAULT_USER_CONTEXT_MAX_CHARS` | 4000 | Default cap for formatted user context block. |
| `agent_prompts.py` | `DEFAULT_NARRATIVE_MAX_CHARS` | 1200 | SOUL + goals shared budget in `format_user_context`. |
| `agent_prompts.py` | `DEFAULT_MAX_RULES` | 12 | Max number of rules to include; extra rules get an "N more rules omitted" line. |
| `__init__.py` | `LLM_SYSTEM_CONTEXT_MAX_CHARS` | 12000 | Hard cap for system context text before assembly. |
| `__init__.py` | `LLM_USER_CONTEXT_MAX_CHARS` | 2500 | Max chars for the formatted user context block passed to `get_system_message`. |
| `__init__.py` | `LLM_HISTORY_MAX_MESSAGES` | 24 | Max non-system messages (tail of conversation) sent to the LLM. |
| `__init__.py` | `LLM_TOOL_RESULT_KEEP_LAST_ROUNDS` | 2 | Number of most recent tool-call rounds whose results are sent in full; older rounds get a placeholder. |

All of the `LLM_*` values in `__init__.py` are configurable via environment variables (see `.env.example` and project-context).

---

## 9. Summary table of efficiency actions

| Action | When | Effect |
|--------|------|--------|
| Send full system message only on first turn | Request has no system message and no prior assistant | Avoids re-sending full context on every turn. |
| Use continuation system message | Request has no system message but has prior assistant | Minimal system tokens on continuation. |
| Truncate system context | First turn, after load | Caps system prompt size (`LLM_SYSTEM_CONTEXT_MAX_CHARS`). |
| Cap user context block | First turn, in `format_user_context` | Limits rules, SOUL, goals (`LLM_USER_CONTEXT_MAX_CHARS`, narrative and rule limits). |
| User skills on demand | Always (instruction in system message) | Model calls `listUserSkills` / `getUserSkill`; no skill text in system message. |
| Model skills on demand | Always (instruction in system message) | Model calls `listSystemSkills` / `getSystemSkill`; no model-specific skill text in system message. |
| `/skill` injection | When last user message is `/skill <name>` | Skill content sent as user message for that turn only. |
| Trim old tool results | Every request before LLM | Only last N rounds of tool results kept in full; older replaced with placeholder. |
| Trim history | Every request before LLM | Only last M non-system messages sent; system messages always kept. |

Together, these actions keep the payload sent to the LLM within a bounded size and avoid redundant or rarely used context in every request.

---

## 10. Next steps for context management

Possible improvements to consider (in no strict order):

- **Relevant workflow:** Introduce helpers that read or build a *reduced* workflow representation (e.g. node ids, types, connections, and only the widget values the model needs) instead of the full ComfyUI API JSON. Use this in tool results (e.g. `getWorkflowInfo`) and anywhere workflow data is sent to the LLM, so we shrink payload size without losing information needed for reasoning.
- **Summarization instead of truncation (preferred direction):** Replace hard truncation with **summarization** that keeps only what is relevant. For system/user context: when content exceeds the cap, produce a short summary (e.g. key rules, current goals, recent decisions) instead of cutting from the start or end. For conversation history: instead of dropping older messages, maintain a compact "summary of the conversation so far" (user intent, workflow changes, decisions) and send that plus the last N messages. Truncation is aggressive and loses information; summarization preserves meaning within a smaller footprint.
- **Tool result summarization:** For tool rounds that are omitted (replaced by the placeholder), store or generate a one-line summary per round (e.g. “addNode added KSampler”) instead of a generic placeholder, so the model retains a minimal trace of what happened in older rounds.
- **Conversation summarization:** When the thread is long, do not only trim to the last N messages; generate or maintain a short "summary of the conversation so far" (what the user wants, what was done, any pending or repeated requests) and inject it as the first user message of the window or as a system addendum. Keep only what is relevant for the next turn; the rest lives in the summary.
- **Observability:** Log or expose (e.g. via response headers or a `?debug=context` flag) the total input size (chars and/or estimated tokens) and which limits were applied (system truncated, user context truncated, tool rounds omitted, history trimmed). Use this to tune defaults and to diagnose context-related failures.