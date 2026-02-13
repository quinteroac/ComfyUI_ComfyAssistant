# Configuration

This guide covers the initial setup of the ComfyUI Assistant: API configuration and optional first-time onboarding.

## API configuration (required)

The assistant needs an LLM provider to generate responses. Configuration is done via a `.env` file in the extension root (`ComfyUI_ComfyAssistant/`).

### 1. Create the .env file

From the extension root:

```bash
cp .env.example .env
```

Edit `.env` with your preferred editor. **Do not commit `.env`** — it is listed in `.gitignore` because it may contain secrets.

### 2. Main variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LLM_PROVIDER` | Optional provider selector: `openai`, `anthropic`, `claude_code`, or `codex`. If unset, backend auto-selects based on available credentials. | No |
| `OPENAI_API_KEY` | API key for OpenAI-compatible provider. Required when using `openai` provider. | Conditional |
| `OPENAI_API_BASE_URL` | Base URL of the API. Change this to use your provider endpoint. | No (default: `https://api.openai.com/v1`) |
| `OPENAI_MODEL` | Model name. Optional; value depends on the provider. | No |
| `ANTHROPIC_API_KEY` | Direct Anthropic API key. Required when using `anthropic` provider. | Conditional |
| `ANTHROPIC_MODEL` | Anthropic model name. | No (default: `claude-sonnet-4-5`) |
| `ANTHROPIC_BASE_URL` | Anthropic API base URL. | No (default: `https://api.anthropic.com`) |
| `ANTHROPIC_MAX_TOKENS` | Max output tokens for Anthropic Messages API calls. | No (default: `4096`) |
| `CLAUDE_CODE_COMMAND` | Claude Code executable name/path. | No (default: `claude`) |
| `CLAUDE_CODE_MODEL` | Optional Claude Code model alias. | No |
| `CODEX_COMMAND` | Codex executable name/path. | No (default: `codex`) |
| `CODEX_MODEL` | Optional Codex model id/alias. | No |
| `GEMINI_CLI_COMMAND` | Gemini CLI executable name/path. | No (default: `gemini`) |
| `GEMINI_CLI_MODEL` | Optional Gemini CLI model name. | No |
| `CLI_PROVIDER_TIMEOUT_SECONDS` | Timeout for CLI providers in seconds. | No (default: `180`) |
| `SEARXNG_URL` | SearXNG instance URL for web search (Phase 8). | No (e.g. `http://localhost:8080`) |
| `LLM_REQUEST_DELAY_SECONDS` | Delay in seconds before each LLM request. Default `1.0`. Increase if you get 429 rate limit errors. | No |
| `LLM_SYSTEM_CONTEXT_MAX_CHARS` | Max characters from `system_context/` injected per request. Default `12000`. | No |
| `LLM_USER_CONTEXT_MAX_CHARS` | Max characters for the formatted user context block. Default `2500`. | No |
| `LLM_HISTORY_MAX_MESSAGES` | Max non-system messages sent to LLM per request. Default `24`. | No |
| `LLM_TOOL_RESULT_KEEP_LAST_ROUNDS` | Number of "rounds" of tool results to keep in full (default: `2`). Older rounds get a short placeholder to reduce context size. | No |
| `COMFY_ASSISTANT_LOG_LEVEL` | Backend log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). Default `INFO`. | No |
| `COMFY_ASSISTANT_DEBUG_CONTEXT` | When `1`, every `/api/chat` response includes context pipeline debug metrics (X-ComfyAssistant-Context-Debug header, context-debug SSE event). Also available per-request via `?debug=context`. Default `0`. | No |

### 3. Example configurations

**OpenAI-compatible:**

```bash
OPENAI_API_KEY=sk_your_api_key_here
OPENAI_API_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-4o-mini
COMFY_ASSISTANT_LOG_LEVEL=INFO
```

**Anthropic with API key:**

```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-your_key_here
# ANTHROPIC_MODEL=claude-sonnet-4-5
```

> Note: `ANTHROPIC_AUTH_TOKEN` from `claude setup-token` does not authenticate direct `api.anthropic.com/v1/messages` calls in this backend path.

**Claude Code CLI (`claude setup-token`):**

```bash
LLM_PROVIDER=claude_code
# Optional
# CLAUDE_CODE_COMMAND=claude
# CLAUDE_CODE_MODEL=sonnet
```

**Codex CLI:**

```bash
LLM_PROVIDER=codex
# Optional
# CODEX_COMMAND=codex
# CODEX_MODEL=o3
```

**Gemini CLI (`gemini login`):**

```bash
LLM_PROVIDER=gemini_cli
# Optional
# GEMINI_CLI_COMMAND=gemini
# GEMINI_CLI_MODEL=auto
```

> `claude_code`, `codex`, and `gemini_cli` providers use structured JSON adapters to emit backend tool calls into the existing frontend tool pipeline. Behavior can vary if CLI output contracts change between versions.

**OpenAI:**

```bash
OPENAI_API_KEY=sk-your_openai_key_here
OPENAI_API_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-4o
```

**Local / Ollama:**

```bash
OPENAI_API_KEY=ollama
OPENAI_API_BASE_URL=http://localhost:11434/v1
# OPENAI_MODEL=llama3.2
```

### 4. Apply changes

After editing `.env`, **restart ComfyUI** so the backend loads the new values.

---

## First-time onboarding (optional)

On first use, the assistant can show a short **onboarding** flow to capture:

- **Personality / tone** — How you want the assistant to sound (e.g. casual, formal).
- **Goals** — What you want to achieve with ComfyUI (e.g. learning, speed, quality).
- **Experience level** — Beginner, intermediate, or advanced.

This information is stored in the **user context** (`user_context/`) and is injected into the system prompt so the assistant adapts to you.

### What happens during onboarding

1. When you open the Assistant tab for the first time, the app may show an onboarding screen instead of the chat.
2. You can fill in the fields or click **Skip** to use neutral defaults.
3. On submit (or skip), the backend writes:
   - `user_context/SOUL.md` — personality/tone
   - `user_context/goals.md` — goals and experience
   - A flag so onboarding is not shown again

After that, the chat is shown and the assistant uses your context when replying.

### Editing context later

You can change personality and goals at any time by editing these files in the extension folder:

- `user_context/SOUL.md`
- `user_context/goals.md`

The assistant reads them on the next request. You do not need to restart ComfyUI for text edits in `user_context/`.

---

## User context workspace

The folder `user_context/` is the assistant’s **user workspace**:

| Path | Purpose |
|------|---------|
| `context.db` | SQLite database: rules, preferences, onboarding flag (created automatically). |
| `SOUL.md` | Personality / tone (from onboarding or manual edit). |
| `goals.md` | Your goals and experience level. |
| `skills/` | User-defined skills — see [User skills](skills.md). |

These files are created on first use (onboarding or first chat). Do not commit `context.db`, `SOUL.md`, `goals.md`, or the contents of `skills/` if they contain personal data; they are in `.gitignore` by default.

---

## Rate limits (429 errors)

Free-tier APIs often rate-limit requests. If you see "Rate limit exceeded" or similar:

1. Wait a minute and try again.
2. In `.env`, increase the delay: e.g. `LLM_REQUEST_DELAY_SECONDS=2.0` or higher.
3. Restart ComfyUI.

This delay is applied before each LLM request and can reduce 429 errors when the assistant makes several tool calls in a row.

---

## Next steps

- [User skills](skills.md) — Add custom instructions the assistant will follow.
- [Base tools](base-tools.md) — What the assistant can do in the workflow and how to ask.
