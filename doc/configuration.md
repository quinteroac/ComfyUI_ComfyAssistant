# Configuration

This guide covers initial setup: provider configuration wizard, optional `.env` fallback, and first-time onboarding.

## Provider configuration wizard (required)

The assistant needs at least one configured provider to generate responses.

### First-time flow

1. Open the Assistant tab.
2. If no providers are configured, the **Provider Wizard** opens in full-page mode.
3. Configure one of: `openai`, `anthropic`, `claude_code`, `codex`, `gemini_cli`.
4. Save and continue to chat.

Provider settings are stored in:

- `user_context/providers.db`
- Table: `providers`
- API keys are stored base64-encoded (local obfuscation only)

### Provider rules

- API providers (`openai`, `anthropic`): multiple named configs allowed.
- CLI providers (`claude_code`, `codex`, `gemini_cli`): one config per type, name must equal provider type.
- Exactly one provider is active at a time.
- Switch active provider at runtime with `/provider set <name>`.

### Open provider settings later

- Slash command: `/provider-settings`
- This opens the wizard in modal mode without interrupting first-time onboarding state.

---

## `.env` fallback (optional)

There is **no migration from `.env` to `providers.db`**.  
If no active DB provider exists, backend still falls back to `.env` values for compatibility.

Common fallback vars:

- `LLM_PROVIDER`
- `OPENAI_API_KEY`, `OPENAI_API_BASE_URL`, `OPENAI_MODEL`
- `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`, `ANTHROPIC_MODEL`, `ANTHROPIC_MAX_TOKENS`
- `CLAUDE_CODE_COMMAND`, `CLAUDE_CODE_MODEL`
- `CODEX_COMMAND`, `CODEX_MODEL`
- `GEMINI_CLI_COMMAND`, `GEMINI_CLI_MODEL`
- `CLI_PROVIDER_TIMEOUT_SECONDS`

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
| `providers.db` | SQLite database: provider configs and active provider selection. |
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
