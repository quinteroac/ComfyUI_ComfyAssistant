# Slash Commands

The assistant supports local slash commands for quick actions. Most commands are handled entirely in the UI and are not sent to the LLM. **Backend-managed commands:** `/skill <name>`, `/provider ...`, and `/persona ...`.

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Show the help message. | `/help` |
| `/clear` | Reset current thread to initial empty state. | `/clear` |
| `/compact [keep]` | Compact context locally and keep only the latest `keep` messages (default: 6). | `/compact 8` |
| `/new` | Create and switch to a new session. | `/new` |
| `/rename <name>` | Rename the current session. | `/rename my-workflow` |
| `/sessions` | List all sessions with index and id. | `/sessions` |
| `/session <id|index|name>` | Switch to a session by id, index (1-based), or exact name. | `/session 2` |
| `/skill <name>` | Activate a user skill by name or slug (e.g. `/skill use-preview-image`). The backend resolves the skill and injects its instructions for this turn only. | `/skill use-preview-image` |
| `/provider-settings` | Open the provider configuration wizard modal. | `/provider-settings` |
| `/provider list` | List configured providers and mark the active one. | `/provider list` |
| `/provider set <name>` | Set the active provider at runtime. | `/provider set openai-main` |
| `/persona` or `/persona list` | List all personas; active one marked with ✓. | `/persona` |
| `/persona <name-or-slug>` | Switch to a persona (and its provider). | `/persona creative-director` |
| `/persona create` | Start the flow to create a new persona (name → description → provider). | `/persona create` |
| `/persona del <name-or-slug>` | Delete a persona. `/persona delete` also works. | `/persona del my-persona` |

## Notes

- `/skill <name>` is handled by the backend; the message is sent to the LLM and the skill content is injected as the user message for that turn. Use **listUserSkills** (or ask the assistant) to see available skill names/slugs.
- `/provider ...` and `/persona ...` are handled by the backend and do not call the LLM. For a full guide to personas, see [Personas](personas.md).
- Session names are case-insensitive matches for `/session <name>`.
- If multiple sessions have the same name, use the index or id shown in `/sessions`.
