# Frontend and UI Guide

This document covers how the React frontend integrates with ComfyUI, the chat UI components, the terminal theme, slash commands, and how to change common things.

> **Agent skills**: For machine-optimized reference, see [`.agents/skills/ui-integration/SKILL.md`](../../.agents/skills/ui-integration/SKILL.md) and [`.agents/skills/assistant-ui/SKILL.md`](../../.agents/skills/assistant-ui/SKILL.md).

---

## How the extension registers in ComfyUI

The frontend is a React application that registers itself as a ComfyUI extension via the bottom panel tab system. The entry point is `ui/src/main.tsx`, which handles three responsibilities:

1. **Wait for ComfyUI** -- `waitForInit()` polls for `window.app` to be available (5-second timeout). ComfyUI's JavaScript runtime must be loaded before the extension can register.
2. **Register extension** -- `window.app.registerExtension()` with a `bottomPanelTabs` configuration that creates an "Assistant" tab.
3. **Mount React** -- `mountReact(container)` creates a React root with StrictMode, TooltipProvider, and Suspense.

```typescript
window.app.registerExtension({
  name: 'comfyui.assistant',
  bottomPanelTabs: [
    {
      id: 'comfyui-assistant',
      title: 'Assistant',
      type: 'custom',
      render: (container) => {
        // Creates #comfyui-assistant-root div
        // Calls mountReact(rootDiv)
      },
      destroy: () => {
        // Cleanup: unmount React root
      }
    }
  ]
})
```

The tab appears in ComfyUI's bottom panel alongside built-in tabs (Queue, Gallery, etc.).

---

## Component map

| File | Purpose |
|------|---------|
| `ui/src/components/assistant-ui/thread.tsx` | Main Thread component: messages, composer, slash command autocomplete, branch picker |
| `ui/src/components/assistant-ui/markdown-text.tsx` | Markdown rendering for assistant messages (syntax highlighting, code blocks) |
| `ui/src/components/assistant-ui/tool-fallback.tsx` | Renders tool call results inline (name, status, expandable details) |
| `ui/src/components/assistant-ui/attachment.tsx` | File attachment display |
| `ui/src/components/assistant-ui/onboarding.tsx` | First-time onboarding flow (personality, goals) |
| `ui/src/components/assistant-ui/thread-list.tsx` | Thread list (hidden in UI; sessions managed via slash commands) |
| `ui/src/components/assistant-ui/terminal-theme.css` | Terminal-style CSS variables and theme |
| `ui/src/components/assistant-ui/tooltip-icon-button.tsx` | Reusable icon button with tooltip |

---

## Terminal theme

The chat uses a terminal/console aesthetic rather than a typical chat bubble UI:

- **User messages**: Prefix `>` (prompt character), dark background `rgba(0, 0, 0, 0.22)`
- **Assistant messages**: Prefix `*` (bullet), no background
- **Empty state**: ASCII logo + "Type a message or /help to get started"
- **Font**: 15px monospace, relaxed leading
- **Prompt column**: 2ch wide (matches `> ` prefix)

Colors are defined as CSS variables in `terminal-theme.css`:
- `--terminal-prompt` -- Prompt/accent color
- `--terminal-dim` -- Secondary/muted text

---

## Message rendering

### Assistant messages

1. **Text parts** are rendered via the `MarkdownText` component. Raw text is hidden; the visible output goes through remark/rehype plugins for markdown rendering with syntax highlighting.
2. **Reasoning parts** appear as collapsible `<details>` blocks with a "Reasoning" summary. These only appear when the LLM uses `<think>` tags.
3. **Tool parts** are rendered via the `ToolFallback` component, which shows the tool name, execution status, and expandable JSON details.

### User messages

Simple text with the `>` prefix. Supports file attachments via `ComposerAttachments`.

### Composer

- Auto-resizing textarea (min 1.75rem height, max 4.5rem)
- Slash command autocomplete (portal-based, positioned above input)
- Send button that toggles to Cancel when the assistant is running
- Shift+Enter for newline, Enter to send

### Branch picker

Shows an "N / M" counter with Previous/Next buttons. Only visible when multiple branches exist (happens when a user edits and resends a previous message).

---

## Slash commands

Slash commands are implemented in the `useSlashCommands()` hook and integrated into the Thread composer.

| Command | Description |
|---------|-------------|
| `/help` | Show available commands and usage tips |
| `/clear` | Reset current thread to initial empty state |
| `/compact [keep]` | Compact context and keep recent messages |
| `/new` | Start a new chat session |
| `/rename <name>` | Rename the current session |
| `/session <id\|index\|name>` | Switch to a session |
| `/sessions` | List all sessions |

### How they work

1. User types `/` in the composer input.
2. The `useSlashCommands()` hook detects the prefix and shows an autocomplete dropdown.
3. The dropdown is portal-based, positioned above the input.
4. Keyboard navigation: ArrowUp/Down to select, Enter/Tab to execute, Escape to dismiss.
5. Commands execute client-side actions (clear messages, switch thread, etc.) -- they don't go to the LLM.

### Adding a new slash command

Add it to the commands list in the `useSlashCommands()` hook. Each command needs:
- `name` -- The command string (e.g., `/mycommand`)
- `description` -- Help text shown in autocomplete
- `execute` -- A function that performs the action

---

## Runtime setup

`ui/src/App.tsx` sets up the assistant-ui runtime stack:

```
App
└── AppContent
    ├── AssistantRuntimeProvider (with useChatRuntime + AssistantChatTransport)
    └── ChatWithTools
        ├── useComfyTools() -- registers tools into ModelContext
        └── Thread -- renders the chat UI
```

- **Onboarding**: `App` checks `/api/user-context/status` on mount. If the user hasn't completed onboarding, it shows the onboarding flow first.
- **Transport**: `AssistantChatTransport({ api: '/api/chat' })` handles SSE communication with the backend.
- **Auto-resubmit**: `sendAutomaticallyWhen: shouldResubmitAfterToolResult` drives the agentic loop. If the last message part is a tool invocation, it automatically resubmits.
- **Tool registration**: `useComfyTools()` hook creates tools via `createTools(context)` and registers them into the `ModelContext`.

---

## `window.app` access patterns

The frontend accesses ComfyUI's JavaScript API through `window.app`:

- **Polling**: `waitForInit()` in `main.tsx` polls until `window.app` is available.
- **Tool context**: `getToolContext()` provides the `window.app` reference to tool implementations.
- **Graph API**: `window.app.graph` for node manipulation (add, remove, connect, query).
- **Canvas refresh**: `window.app.graph.setDirtyCanvas(true, true)` to trigger re-render after changes.

Key `window.app` methods used by tools:

| Method | Purpose |
|--------|---------|
| `app.registerExtension()` | Register the extension |
| `app.graph.add()` | Add node to graph |
| `app.graph.remove()` | Remove node from graph |
| `app.graph.getNodeById()` | Find node by ID |
| `app.graph.setDirtyCanvas()` | Trigger canvas redraw |
| `app.graph._nodes` | Access node list (read) |
| `app.queuePrompt()` | Queue workflow for execution |

---

## How to change common things

| I want to change... | Edit this file | What to modify |
|---------------------|----------------|----------------|
| Tab name or placement | `ui/src/main.tsx` | `bottomPanelTabs` in `registerExtension()` |
| Message appearance | `ui/src/components/assistant-ui/thread.tsx` | `AssistantMessage` or `UserMessage` component |
| Markdown rendering | `ui/src/components/assistant-ui/markdown-text.tsx` | `MarkdownText` component, remark/rehype plugins |
| Tool result display | `ui/src/components/assistant-ui/tool-fallback.tsx` | `ToolFallback` component |
| Theme colors | `ui/src/components/assistant-ui/terminal-theme.css` | CSS custom properties |
| Empty state / ASCII logo | `ui/src/components/assistant-ui/thread.tsx` | `ThreadEmpty` component |
| Composer behavior | `ui/src/components/assistant-ui/thread.tsx` | `Composer` component and slash command integration |
| Onboarding flow | `ui/src/components/assistant-ui/onboarding.tsx` | `Onboarding` component |
| Slash commands | `ui/src/components/assistant-ui/thread.tsx` | `useSlashCommands()` hook |
| Transport/API endpoint | `ui/src/App.tsx` | `AssistantChatTransport` configuration |
| Agentic loop behavior | `ui/src/App.tsx` | `shouldResubmitAfterToolResult` function |

---

## How do I...

**...add a new UI panel or control?**
Add more entries to the `bottomPanelTabs` array in `main.tsx`, or use ComfyUI's other registration APIs (menu items, sidebar tabs, etc.) in the same `registerExtension()` call.

**...add a new message part type?**
Add a new component and include it in the `MessagePrimitive.Parts` rendering in `AssistantMessage` within `thread.tsx`.

**...access ComfyUI APIs from a new component?**
Use the tool context pattern: call `getToolContext()` which provides the `window.app` reference. All graph manipulation should go through `window.app.graph`.

**...change how the thread list works?**
`thread-list.tsx` exists but the thread list is hidden in the UI. Sessions are managed via slash commands (`/new`, `/session`, `/sessions`, `/rename`). To show a visual thread list, integrate the `ThreadList` component into the layout.

**...build the frontend after changes?**
Run `cd ui && npm run build`. The built files go to `dist/` and are served by ComfyUI.

---

## Related docs

- [Architecture](architecture.md) -- Where the frontend fits in the system
- [Backend](backend.md) -- API endpoints the frontend talks to
- [Tools](tools.md) -- Tool definitions and implementations
- [Context and environment](context-and-environment.md) -- Onboarding data and environment queries
- [Standards and conventions](standards-and-conventions.md) -- TypeScript style, React patterns
