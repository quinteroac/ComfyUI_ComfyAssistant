# Phase 5b: Slash Commands & Named Sessions

## Context

Phase 5a (done) moved the assistant to a bottom panel with terminal aesthetics. The composer shows a `comfy>` prompt and the welcome screen says "Type a message or /help to get started" — but slash commands don't exist yet. Phase 5b adds them.

**Scope:** `/help`, `/clear`, `/new`, `/rename <name>`, `/sessions`. `/settings` deferred to later.

**Key discovery:** The `@assistant-ui/react@0.12.9` API provides:
- `useAssistantApi()` → `api.thread().append(msg)` with `startRun: false` to add local-only messages
- `api.thread().composer.setText()` / `.send()` for composer control
- `api.threads().switchToNewThread()`, `.item({id}).rename(title)`, `.item({id}).switchTo()` for thread management
- `api.thread().reset()` to clear thread messages

---

## Plan

### Step 1: Create slash command registry

**Create:** `ui/src/slash-commands/registry.ts`

Define a `SlashCommand` type and a static registry array:

```typescript
export interface SlashCommand {
  name: string           // e.g. "help"
  description: string    // short one-liner
  usage: string          // e.g. "/rename <name>"
  execute: (args: string, ctx: SlashCommandContext) => void
}

export interface SlashCommandContext {
  threadApi: ThreadMethods      // from useAssistantApi().thread()
  threadsApi: ThreadsMethods    // from useAssistantApi().threads()
  appendLocal: (text: string) => void  // helper: append assistant msg with startRun:false
}
```

Register all commands in a `COMMANDS` array exported from this file.

### Step 2: Implement command handlers

**Create:** `ui/src/slash-commands/commands.ts`

Individual command implementations:

#### `/help`
- `appendLocal()` a formatted message listing all registered commands with descriptions
- Format as a compact markdown table or list

#### `/clear`
- Call `threadApi.reset()` to clear all messages from the current thread
- The thread stays (not deleted), just emptied

#### `/new`
- Call `threadsApi.switchToNewThread()` to create and switch to a fresh thread

#### `/rename <name>`
- Parse `<name>` from args (everything after `/rename `)
- Get current thread ID via `threadsApi.getState().mainThreadId`
- Call `threadsApi.item({ id }).rename(name)`
- `appendLocal()` confirmation: `Session renamed to "<name>"`
- If no name provided, `appendLocal()` usage hint

#### `/sessions`
- Read `threadsApi.getState().threadIds` and iterate `.item({id}).getState()` to get titles
- `appendLocal()` a formatted list of sessions with IDs/titles
- Mark the current session

### Step 3: Create the `useSlashCommands` hook

**Create:** `ui/src/hooks/useSlashCommands.ts`

```typescript
export function useSlashCommands() {
  const api = useAssistantApi()

  const appendLocal = (text: string) => {
    api.thread().append({
      role: 'assistant',
      content: [{ type: 'text', text }],
      startRun: false
    })
  }

  const ctx: SlashCommandContext = {
    threadApi: api.thread(),
    threadsApi: api.threads(),
    appendLocal
  }

  /** Returns true if the input was handled as a command */
  const tryExecute = (input: string): boolean => {
    const trimmed = input.trim()
    if (!trimmed.startsWith('/')) return false

    const spaceIdx = trimmed.indexOf(' ')
    const name = (spaceIdx === -1 ? trimmed.slice(1) : trimmed.slice(1, spaceIdx)).toLowerCase()
    const args = spaceIdx === -1 ? '' : trimmed.slice(spaceIdx + 1).trim()

    const cmd = COMMANDS.find(c => c.name === name)
    if (!cmd) {
      appendLocal(`Unknown command: /${name}. Type /help for available commands.`)
      return true
    }

    cmd.execute(args, ctx)
    return true
  }

  /** Returns matching commands for autocomplete */
  const getSuggestions = (input: string): SlashCommand[] => {
    if (!input.startsWith('/')) return []
    const partial = input.slice(1).toLowerCase()
    return COMMANDS.filter(c => c.name.startsWith(partial))
  }

  return { tryExecute, getSuggestions }
}
```

### Step 4: Intercept composer submission

**Modify:** `ui/src/components/assistant-ui/thread.tsx`

Wrap the `Composer` component to intercept `/` commands before they reach the LLM:

```tsx
const Composer: FC = () => {
  const { tryExecute } = useSlashCommands()
  const api = useAssistantApi()

  const handleSubmit = () => {
    const text = api.thread().composer.getState().text
    if (tryExecute(text)) {
      api.thread().composer.setText('')
      return  // handled locally, don't send to LLM
    }
    // Not a command — let default send behavior proceed
    api.thread().composer.send()
  }

  return (
    <ComposerPrimitive.Root onSubmit={handleSubmit} ...>
      ...
    </ComposerPrimitive.Root>
  )
}
```

Key: `ComposerPrimitive.Root` accepts an `onSubmit` handler. When we call it, we prevent default and handle locally for commands. For normal messages, we call `composer.send()`.

### Step 5: Add inline autocomplete popup

**Modify:** `ui/src/components/assistant-ui/thread.tsx` (inside Composer)

Add a small autocomplete dropdown that appears when the user types `/`:

- Use `useAssistantState(s => s.composer.text)` to reactively watch composer text
- When text starts with `/`, show a small popup above the input with matching commands
- Each suggestion shows command name + description
- Click or Enter selects a suggestion (fills command into input)
- Popup is a simple positioned `<div>` with `absolute` positioning — no external lib needed
- Keep it minimal: just a `<ul>` with hover states, same terminal styling

### Step 6: Add rename to thread list item context menu

**Modify:** `ui/src/components/assistant-ui/thread-list.tsx`

Add a "Rename" option to the `ThreadListItemMore` dropdown menu:

- Add a `PencilIcon` + "Rename" menu item
- On click: prompt via `window.prompt()` (simple, no modal component needed)
- Call `threadsApi.item({ id }).rename(newTitle)` with the entered name
- This gives users a mouse-based rename in addition to `/rename`

### Step 7: Documentation

- Create `development/phase_5b/implemented.md`
- Update `planning/comfyui_assistant_development_phases.md` (mark 5b done)
- Update `.agents/project-context.md` (mention slash commands)

---

## Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `ui/src/slash-commands/registry.ts` | Create | SlashCommand type + COMMANDS array |
| `ui/src/slash-commands/commands.ts` | Create | /help, /clear, /new, /rename, /sessions |
| `ui/src/slash-commands/index.ts` | Create | Barrel export |
| `ui/src/hooks/useSlashCommands.ts` | Create | Hook: tryExecute + getSuggestions |
| `ui/src/components/assistant-ui/thread.tsx` | Modify | Intercept composer, autocomplete popup |
| `ui/src/components/assistant-ui/thread-list.tsx` | Modify | Add rename menu item |
| `development/phase_5b/implemented.md` | Create | Phase record |
| `planning/comfyui_assistant_development_phases.md` | Update | Mark 5b done |
| `.agents/project-context.md` | Update | Mention slash commands |

---

## API References

- `useAssistantApi()` → returns `AssistantClient` — `ui/node_modules/@assistant-ui/store/dist/useAui.d.ts`
- `ThreadMethods.append(msg)` — `node_modules/@assistant-ui/react/src/types/scopes/thread.ts:89`
- `ThreadMethods.reset()` — `node_modules/@assistant-ui/react/src/types/scopes/thread.ts:108`
- `ThreadsMethods.switchToNewThread()` — `node_modules/@assistant-ui/react/src/types/scopes/threads.ts:21`
- `ThreadListItemMethods.rename(title)` — `node_modules/@assistant-ui/react/src/types/scopes/threadListItem.ts:15`
- `ComposerMethods.setText()` / `.send()` — `node_modules/@assistant-ui/react/src/types/scopes/composer.ts:27,34`
- `CreateAppendMessage.startRun` — `node_modules/@assistant-ui/react/src/legacy-runtime/runtime/ThreadRuntime.ts:79`

---

## Risks

1. **`startRun: false`**: Not explicitly documented but present in the type. If it doesn't prevent LLM call, fallback: append as `role: "user"` and immediately `cancelRun()`.
2. **`ComposerPrimitive.Root onSubmit`**: If the primitive doesn't support `onSubmit`, wrap the textarea `onKeyDown` to intercept Enter.
3. **Thread rename persistence**: Rename may not persist across reloads if the chat runtime doesn't have a persistence layer. This is acceptable — thread naming is best-effort for this phase.

---

## Verification

1. `cd ui && npm run typecheck` — no TS errors
2. `cd ui && npm run lint` — no lint errors
3. `cd ui && npm run build` — builds successfully
4. In ComfyUI browser:
   - Type `/help` → see formatted command list as assistant message, no LLM call
   - Type `/clear` → thread messages cleared
   - Type `/new` → switches to new empty thread
   - Type `/rename my-session` → thread tab updates with name
   - Type `/sessions` → see list of sessions
   - Type `/unknown` → see "Unknown command" message
   - Type `/` → autocomplete popup appears with command suggestions
   - Normal messages still sent to LLM as before
   - Right-click thread tab → Rename option works
