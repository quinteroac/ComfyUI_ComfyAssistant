# Personas

Personas let you switch between named personalities for the assistant. Each persona is tied to a **provider** (e.g. OpenAI, Anthropic, Grok) and has its own tone, style, and instructions. When you switch persona, the assistant uses that persona’s text and the associated provider for the next messages.

## Prerequisites

- At least one provider must be configured (see [Configuration](configuration.md)).
- The persona’s **Provider** (in its file) must match a configured provider name.

## Slash commands

| Command | Description |
|--------|-------------|
| `/persona` or `/persona list` | List all personas. The active one is marked with ✓. |
| `/persona <name-or-slug>` | Switch to a persona by display name or slug (e.g. `/persona creative-director`). The provider is switched to the one set in the persona. |
| `/persona create` | Start the conversational flow to create a new persona (name → description → provider). You can also type “create persona” or “new persona” to start it. |
| `/persona del <name-or-slug>` | Delete a persona. If it was the active one, the assistant falls back to the default personality. `/persona delete` is also accepted. |

All persona commands are handled by the backend (no LLM call for list/switch/delete).

## Creating a persona with `/persona create`

1. Type `/persona create` (or “create persona”, “new persona”) and send.
2. **Name:** Enter a short name (e.g. “Creative Director”). It will be slugified (e.g. `creative-director`) for the folder name.
3. **Description:** Enter a short description of the personality (behavior, background, specialty).
4. **Provider:** Choose one of the configured providers from the list. That provider will be used when this persona is active.
5. The persona is created, set as active, and the provider is switched. New messages use this persona.

To cancel the flow, send `/cancel` or “cancel” before finishing.

## Where personas are stored

Each persona lives in its own folder:

```
user_context/personas/<persona-slug>/SOUL.md
```

- `<persona-slug>` must be a valid slug (letters, numbers, hyphens; e.g. `creative-director`).
- Each folder contains exactly one `SOUL.md`.
- The file is loaded when this persona is active (`preferences.active_persona` = slug).

## File format

`SOUL.md` must start with **YAML frontmatter** with three fields, then free-text instructions:

| Field | Required | Description |
|-------|----------|-------------|
| `Name` | Yes | Display name (e.g. “Creative Director”). |
| `Description` | Yes | Short description of the persona. |
| `Provider` | Yes | Must match a configured provider name in `providers.db` (e.g. `openai-main`, `grok`). |

After the frontmatter (after the second `---`), add the personality instructions in Markdown. This text is injected into the system prompt when the persona is active.

### Example

```markdown
---
Name: Creative Director
Description: Cinematic visual storyteller for concept workflows
Provider: openai-main
---

You are a cinematic creative director. Speak in concise actionable steps, and
prioritize composition, lighting, and mood consistency in workflow suggestions.
```

## Creating or editing a persona manually

1. Create a folder: `user_context/personas/<slug>/` (e.g. `user_context/personas/my-persona/`).
2. Add `SOUL.md` with the YAML frontmatter and body as above.
3. To use it: `/persona <name-or-slug>` (use the `Name` from frontmatter or the slug).

You can edit `SOUL.md` with a text editor anytime; changes apply on the next message. You do not need to restart ComfyUI.

## Switching and active persona

- **Switch:** `/persona <name-or-slug>` activates that persona and switches the provider to the one in its frontmatter.
- **No persona:** If you have never set a persona, or you delete the active one, the assistant uses the default personality (and the current provider). Legacy `user_context/SOUL.md` is used as fallback when no persona is active.
- **Provider mismatch:** If a persona’s provider is not configured, the switch fails with a message; configure that provider in `/provider-settings` first.

## See also

- [Configuration](configuration.md) — Provider setup and user context overview.
- [Slash commands](commands.md) — Full list of commands.
