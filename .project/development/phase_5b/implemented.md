# Phase 5b: Slash Commands & Named Sessions

**Status**: Implemented
**Branch**: `feature/phase-5b-slash-commands`

## Summary

Added slash commands (`/help`, `/clear`, `/new`, `/rename`, `/sessions`), inline autocomplete when typing `/`, and a Rename option in the thread list dropdown.

## Changes

### Slash Command Registry
- **`ui/src/slash-commands/registry.ts`** — `SlashCommand` interface and registry
- **`ui/src/slash-commands/types.ts`** — `SlashCommandContext` type
- **`ui/src/slash-commands/commands.ts`** — Command implementations:
  - `/help` — Lists available commands in a markdown table
  - `/clear` — Clears all messages in the current thread
  - `/new` — Creates and switches to a new session
  - `/rename <name>` — Renames the current session
  - `/sessions` — Lists all sessions with the current one marked

### useSlashCommands Hook
- **`ui/src/hooks/useSlashCommands.ts`** — Hook providing:
  - `tryExecute(input)` — Parses and executes slash commands; returns true if handled
  - `getSuggestions(input)` — Returns matching commands for autocomplete

### Composer Integration
- **`ui/src/components/assistant-ui/thread.tsx`**:
  - Intercepts submit (Enter and Send button) to check for slash commands before sending to LLM
  - Uses `submitOnEnter={false}` and custom `handleSubmit` for full control
  - Autocomplete popup when typing `/`: shows command name + description
  - Arrow Up/Down to navigate, Enter/Tab to select
  - Replaced `ComposerPrimitive.Send` with custom button that calls `handleSubmit`

### Thread List Rename
- **`ui/src/components/assistant-ui/thread-list.tsx`**:
  - Added "Rename" menu item with PencilIcon in `ThreadListItemMore` dropdown
  - On select: `window.prompt()` for new name, then `threadsApi.item({ id }).rename(newTitle)`

## Technical Notes

- Commands append local-only assistant messages via `startRun: false` to avoid LLM calls
- Slash command parsing: `/name` or `/name args`; name is case-insensitive
- Autocomplete uses `useAssistantState(s => s.composer.text)` for reactive composer text
- Rename persistence is best-effort (depends on assistant-ui runtime persistence)

## Files Changed

| File | Action |
|------|--------|
| `ui/src/slash-commands/registry.ts` | Created |
| `ui/src/slash-commands/types.ts` | Created |
| `ui/src/slash-commands/commands.ts` | Created |
| `ui/src/slash-commands/index.ts` | Created |
| `ui/src/hooks/useSlashCommands.ts` | Created |
| `ui/src/components/assistant-ui/thread.tsx` | Modified |
| `ui/src/components/assistant-ui/thread-list.tsx` | Modified |
