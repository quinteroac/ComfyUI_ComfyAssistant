# Slash Commands

The assistant supports local slash commands for quick actions. Most commands are handled entirely in the UI and are not sent to the LLM. **Exception:** `/skill <name>` is sent to the backend, which resolves the skill and injects its instructions for that turn.

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

## Notes

- `/skill <name>` is handled by the backend; the message is sent to the LLM and the skill content is injected as the user message for that turn. Use **listUserSkills** (or ask the assistant) to see available skill names/slugs.
- Session names are case-insensitive matches for `/session <name>`.
- If multiple sessions have the same name, use the index or id shown in `/sessions`.
