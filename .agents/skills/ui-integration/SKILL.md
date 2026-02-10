---
name: ui-integration
description: How the React extension wires into ComfyUI -- entry point, bottom panel, window.app access
version: 0.0.1
license: MIT
---

# UI Integration

This skill explains how the React frontend registers itself as a ComfyUI extension and integrates with the host application.

## Entry Point: `ui/src/main.tsx`

The entry point handles three responsibilities:

1. **Wait for ComfyUI** -- `waitForInit()` polls for `window.app` to be available (5-second timeout)
2. **Register extension** -- `window.app.registerExtension()` with `bottomPanelTabs` configuration
3. **Mount React** -- `mountReact(container)` creates a React root with StrictMode, TooltipProvider, and Suspense

### Bottom Panel Registration

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

## How to Change Tab Name/Placement

- **Tab title**: Change the `title` property in `bottomPanelTabs` in `main.tsx`
- **Tab ID**: Change the `id` property (must be unique across extensions)
- **Panel type**: Currently `'custom'` with full React rendering; `type` controls ComfyUI's rendering behavior

## `window.app` Access

The frontend accesses ComfyUI's JavaScript API via `window.app`:

- **Polling**: `waitForInit()` in `main.tsx` polls until `window.app` is available
- **Tool context**: `getToolContext()` provides `window.app` reference to tool implementations
- **Graph API**: `window.app.graph` for node manipulation (add, remove, connect, query)
- **Canvas**: `window.app.graph.setDirtyCanvas(true, true)` to trigger re-render after changes

### Key `window.app` Methods Used

| Method | Purpose |
|--------|---------|
| `app.registerExtension()` | Register the extension |
| `app.graph.add()` | Add node to graph |
| `app.graph.remove()` | Remove node from graph |
| `app.graph.getNodeById()` | Find node by ID |
| `app.graph.setDirtyCanvas()` | Trigger canvas redraw |
| `app.graph._nodes` | Access node list (read) |
| `app.queuePrompt()` | Queue workflow for execution |

## Slash Commands System

Implemented in `useSlashCommands()` hook, integrated into the Thread composer:

| Command | Description |
|---------|-------------|
| `/help` | Show available commands and usage tips |
| `/clear` | Clear current thread messages |
| `/new` | Start a new chat session |
| `/rename <name>` | Rename the current session |
| `/session <id\|index\|name>` | Switch to a session |
| `/sessions` | List all sessions |

### How Slash Commands Work

1. User types `/` in the composer input
2. `useSlashCommands()` hook detects the prefix and shows autocomplete dropdown
3. Autocomplete is portal-based, positioned above the input
4. Keyboard navigation: ArrowUp/Down to select, Enter/Tab to execute, Escape to dismiss
5. Commands execute client-side actions (clear messages, switch thread, etc.)

## App Component Architecture

`ui/src/App.tsx` sets up the runtime stack:

```
App
└── AppContent
    ├── AssistantRuntimeProvider (with useChatRuntime + AssistantChatTransport)
    └── ChatWithTools
        ├── useComfyTools() -- registers tools into ModelContext
        └── Thread -- renders the chat UI
```

- **Onboarding**: `App` checks `/api/user-context/status` on mount; shows onboarding flow if needed
- **Transport**: `AssistantChatTransport({ api: '/api/chat' })` handles SSE communication
- **Auto-resubmit**: `sendAutomaticallyWhen: shouldResubmitAfterToolResult` drives the agentic loop

## FAQ

### Where do I change the tab name/icon/placement?
In `ui/src/main.tsx`, modify the `bottomPanelTabs` array in `registerExtension()`. Change `title` for the name, `id` for the identifier.

### How do I add new UI panels or controls?
Add more entries to the `bottomPanelTabs` array in `main.tsx`, or use ComfyUI's other registration APIs (menu items, sidebar tabs, etc.) in the same `registerExtension()` call.

### How do I add a new slash command?
Add it to the commands list in the `useSlashCommands()` hook. Each command needs a name, description, and execute function.

### How do I access ComfyUI APIs from a new component?
Use the tool context pattern: call `getToolContext()` which provides `window.app` reference. All graph manipulation should go through `window.app.graph`.

## Related Skills

- `assistant-ui` -- chat UI components and customization
- `architecture-overview` -- where UI integration fits in the system
- `backend-architecture` -- the API endpoints the frontend talks to
