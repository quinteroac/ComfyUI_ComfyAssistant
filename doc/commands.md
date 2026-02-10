# Slash Commands

The assistant supports local slash commands for quick actions. These commands are handled entirely in the UI and are not sent to the LLM.

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Show the help message. | `/help` |
| `/clear` | Clear all messages in the current thread. | `/clear` |
| `/new` | Create and switch to a new session. | `/new` |
| `/rename <name>` | Rename the current session. | `/rename my-workflow` |
| `/sessions` | List all sessions with index and id. | `/sessions` |
| `/session <id|index|name>` | Switch to a session by id, index (1-based), or exact name. | `/session 2` |

## Notes

- Session names are case-insensitive matches for `/session <name>`.
- If multiple sessions have the same name, use the index or id shown in `/sessions`.
