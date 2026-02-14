---
name: assistant-ui
description: Project-specific guide for the chat UI -- components, terminal theme, message rendering, runtime setup
version: 0.0.1
license: MIT
---

# assistant-ui (Project-Specific)

How ComfyUI Assistant uses the assistant-ui library. For generic library reference, see `./references/`.

## Component Map

| File | Purpose |
|------|---------|
| `ui/src/components/assistant-ui/thread.tsx` | Main Thread component: messages, composer, slash command autocomplete, branch picker |
| `ui/src/components/assistant-ui/markdown-text.tsx` | Markdown rendering for assistant messages (syntax highlighting, code blocks) |
| `ui/src/components/assistant-ui/tool-fallback.tsx` | Renders tool calls as terminal log lines (prefix `›`, name, status icon); details (args, result, error) expand on click |
| `ui/src/components/assistant-ui/attachment.tsx` | File attachment display |
| `ui/src/components/assistant-ui/onboarding.tsx` | First-time onboarding flow (personality, goals) |
| `ui/src/components/assistant-ui/thread-list.tsx` | Thread list (hidden in UI; sessions managed via slash commands) |
| `ui/src/components/assistant-ui/terminal-theme.css` | Terminal-style CSS variables and theme |
| `ui/src/components/assistant-ui/tooltip-icon-button.tsx` | Reusable icon button with tooltip |

## Console-Style Terminal Layout

The chat uses a terminal aesthetic, not a typical chat bubble UI:

- **User messages**: Prefix `>` (prompt character), dark background `rgba(0, 0, 0, 0.22)`
- **Assistant messages**: Prefix `*` (bullet), no background
- **Empty state**: ASCII logo + "Type a message or /help to get started"
- **Font**: 15px monospace, relaxed leading
- **Colors**: CSS variables in `terminal-theme.css`
  - `--terminal-prompt`: prompt/accent color
  - `--terminal-dim`: secondary/muted text
- **Prompt column**: 2ch wide (matches "> " prefix)

## Message Rendering

### Assistant Messages
1. **Text parts**: Rendered via `MarkdownText` component (hidden raw text, visible markdown)
2. **Reasoning parts**: Collapsible `<details>` block with "Reasoning" summary
3. **Tool parts**: Rendered via `ToolFallback` component. Each tool appears as a single terminal-style log line (prefix `›`, status icon, tool name, chevron). Collapsed by default; click to expand args, result, or error. Styling matches terminal dim/foreground; no card or box so the chat stays readable.

### User Messages
- Simple text with `>` prefix
- Supports attachments (ComposerAttachments)

### Composer
- Auto-resizing textarea (min 1.75rem, max 4.5rem)
- Slash command autocomplete (portal-based, positioned above input)
- Send button (toggles to Cancel when running)
- Shift+Enter for newline, Enter to send

### Branch Picker
- Shows "N / M" counter with Previous/Next buttons
- Only visible when multiple branches exist

## Where to Change Things

| Change | File | What to Edit |
|--------|------|-------------|
| Message appearance | `thread.tsx` | `AssistantMessage` or `UserMessage` component |
| Markdown rendering | `markdown-text.tsx` | `MarkdownText` component, remark/rehype plugins |
| Tool result display | `tool-fallback.tsx` | `ToolFallback` component |
| Theme colors | `terminal-theme.css` | CSS custom properties |
| Empty state / ASCII logo | `thread.tsx` | `ThreadEmpty` component |
| Composer behavior | `thread.tsx` | `Composer` component and slash command integration |
| Onboarding flow | `onboarding.tsx` | `Onboarding` component |
| Bottom panel config | `main.tsx` | `bottomPanelTabs` in `registerExtension()` |

## Runtime Setup in `App.tsx`

```
AssistantRuntimeProvider
  runtime = useChatRuntime({
    transport: AssistantChatTransport({ api: '/api/chat' }),
    sendAutomaticallyWhen: shouldResubmitAfterToolResult
  })
  └── ChatWithTools
      ├── useComfyTools() → registers tools into ModelContext
      └── Thread
```

- **Transport**: `AssistantChatTransport` handles SSE communication with `/api/chat`
- **Auto-resubmit**: `shouldResubmitAfterToolResult` checks if the last message part is a tool invocation; if so, automatically resubmits for the next LLM response
- **Tool registration**: `useComfyTools()` hook creates tools via `createTools(context)` and registers them

## References

- [./references/architecture.md](./references/architecture.md) -- Core assistant-ui library architecture and layered system
- [./references/packages.md](./references/packages.md) -- Package overview and selection guide

## FAQ

### Where do I change how messages look?
Edit `AssistantMessage` or `UserMessage` in `thread.tsx`. For markdown rendering, edit `markdown-text.tsx`. For tool results, edit `tool-fallback.tsx`.

### Where do I change the theme or colors?
Edit `terminal-theme.css`. The main variables are `--terminal-prompt` (accent) and `--terminal-dim` (muted).

### How do I add a new message part type?
Add a new component and include it in the `MessagePrimitive.Parts` rendering in `AssistantMessage` within `thread.tsx`.

### How do I change the bottom panel tab?
Edit `main.tsx` -- modify the `bottomPanelTabs` configuration in `registerExtension()`. See `ui-integration` skill for details.

### Where is the thread list?
`thread-list.tsx` exists but the thread list is hidden in the UI. Sessions are managed via slash commands (`/new`, `/session`, `/sessions`, `/rename`).

## Related Skills

- `ui-integration` -- how the React app registers with ComfyUI
- `architecture-overview` -- runtime and agentic loop explanation
- `backend-tools-declaration` -- tool definitions that drive ToolFallback rendering
