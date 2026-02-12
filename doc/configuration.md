# Configuration

This guide covers the initial setup of the ComfyUI Assistant: API configuration and optional first-time onboarding.

## API configuration (required)

The assistant needs an OpenAI-compatible API to generate responses. Configuration is done via a `.env` file in the extension root (`ComfyUI_ComfyAssistant/`).

### 1. Create the .env file

From the extension root:

```bash
cp .env.example .env
```

Edit `.env` with your preferred editor. **Do not commit `.env`** — it is listed in `.gitignore` because it may contain secrets.

### 2. Main variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | API key for the LLM provider. | **Yes** |
| `OPENAI_API_BASE_URL` | Base URL of the API. Change this to use your provider endpoint. | No (default: `https://api.openai.com/v1`) |
| `OPENAI_MODEL` | Model name. Optional; value depends on the provider. | No |
| `LLM_REQUEST_DELAY_SECONDS` | Delay in seconds before each LLM request. Default `1.0`. Increase if you get 429 rate limit errors. | No |
| `LLM_SYSTEM_CONTEXT_MAX_CHARS` | Max characters from `system_context/` injected per request. Default `12000`. | No |
| `LLM_USER_CONTEXT_MAX_CHARS` | Max characters for the formatted user context block. Default `2500`. | No |
| `LLM_HISTORY_MAX_MESSAGES` | Max non-system messages sent to LLM per request. Default `24`. | No |
| `COMFY_ASSISTANT_LOG_LEVEL` | Backend log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). Default `INFO`. | No |

### 3. Example configurations

**Default endpoint:**

```bash
OPENAI_API_KEY=sk_your_api_key_here
OPENAI_API_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-4o-mini
COMFY_ASSISTANT_LOG_LEVEL=INFO
```

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
