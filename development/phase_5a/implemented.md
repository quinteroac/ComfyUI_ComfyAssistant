# Phase 5a: Bottom Panel + Terminal Aesthetic

**Status**: Implemented
**Branch**: `feature/phase-5a-bottom-panel`

## Summary

Moved the ComfyUI Assistant from a sidebar tab to a bottom panel tab with a terminal/console-style UI aesthetic. Iterated the terminal theme to match ComfyUI’s console look (monospace, flat blocks, darker base) and stabilized scroll behavior in the panel container.

## Changes

### Layout: Sidebar to Bottom Panel
- `main.tsx`: Replaced `extensionManager.registerSidebarTab()` with `bottomPanelTabs` array inside `registerExtension()`
- Added `destroy()` callback for proper React unmounting
- Sidebar fallback kept as commented-out code for older ComfyUI versions

### Bug Fix: CSS Root ID Mismatch
- All 3 CSS files used `#comfyui-react-example-root` but container was created with `id="comfyui-assistant-root"`
- Fixed by replacing all occurrences in CSS to match the actual container ID

### Terminal UI Aesthetic
- **Font**: Monospace stack (ui-monospace, SF Mono, Menlo, Monaco, Consolas)
- **Font size**: 18px base, line-height 1.4–1.45
- **Messages**: Flat layout (no chat bubbles), `›` prefix for user, `•` for assistant
- **Composer**: Terminal prompt style with `›` prefix, single-line-by-default textarea
- **Spacing**: Compact (py-0.5 on messages instead of py-3)
- **Border-radius**: 0 (flat console blocks)
- **Transitions**: Snappy 100ms instead of 200-300ms
- **Reasoning blocks**: Compact `[thinking...]` collapsible
- **Backgrounds**: Uniform black base, user messages use a lighter gray block (`#6c757d`)

### Thread List: Horizontal Tab Bar
- Converted from vertical list to horizontal tab bar (`flex-row h-8 overflow-x-auto`)
- "New Thread" button: compact `+` icon only
- Thread items: horizontal tab pills (`h-7 px-2 text-xs max-w-[120px]`)
- Removed vertical skeleton loader
### Thread List UI Removal (current iteration)
- Thread list UI and new chat button removed from the view; sessions are intended to be managed via slash commands.
### Slash Commands (current iteration)
- Added `/session <id|index|name>` to switch sessions; `/sessions` now prints an index plus ids alongside titles.

### Welcome Screen
- Replaced "Hello there!" with a Unicode ComfyUI logo block
- Shows "Type a message or /help to get started"
### Scroll Behavior Fix
- Forced the bottom panel container to flex column with `height: 100%` and `overflow: hidden` so the message viewport scrolls correctly while the composer stays pinned.

### CSS Consolidation
- Created `terminal-theme.css` (consolidated from `assistant-ui-theme.css` + `chat-styles.css`)
- Deleted `assistant-ui-theme.css` and `chat-styles.css`
- Deleted empty `App.css`
- Added terminal CSS variables: `--terminal-prompt`, `--terminal-dim`, `--terminal-accent`

### Markdown Rendering
- Tighter spacing: headings, lists, paragraphs use `my-1` instead of `my-2.5`
- Tables use `text-xs` with compact padding
- Code headers use `text-[10px]`

## Files Changed

| File | Action |
|------|--------|
| `ui/src/main.tsx` | Modified (sidebar -> bottom panel) |
| `ui/src/index.css` | Modified (root ID fix, monospace font, terminal vars) |
| `ui/src/components/assistant-ui/terminal-theme.css` | Created, then iterated (console-style refinements, scroll layout, user block) |
| `ui/src/components/assistant-ui/assistant-ui-theme.css` | Deleted |
| `ui/src/components/assistant-ui/chat-styles.css` | Deleted |
| `ui/src/components/assistant-ui/thread.tsx` | Modified (terminal style, prefixes, Unicode logo) |
| `ui/src/components/assistant-ui/thread-list.tsx` | Modified (horizontal tabs), then hidden from UI |
| `ui/src/components/assistant-ui/markdown-text.tsx` | Modified (compact spacing) |
| `ui/src/App.tsx` | Modified (removed App.css import) |
| `ui/src/App.css` | Deleted |
| `.agents/project-context.md` | Updated (sidebar -> bottom panel refs) |

## Next: Phase 5b (done)

- Slash commands (`/help`, `/clear`, `/new`, `/rename`, `/sessions`)
- Named sessions
- Autocomplete and Rename in thread dropdown
