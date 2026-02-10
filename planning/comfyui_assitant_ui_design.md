# ComfyUI Assistant — UI design (terminal-style)

This document describes the target **assistant UI**: a terminal/console-style experience similar to Claude Code or Gemini CLI, integrated into ComfyUI. It is planned for **Phase 5** of development.

---

## Design direction

- **Aesthetic:** Terminal/console feel — monospace-friendly, command-driven, with a clear “session” metaphor. Icons and rich content are still supported where useful.
- **Placement:** Reuse the same pattern as ComfyUI’s **Console** button: a panel that opens at the **bottom** of the ComfyUI UI. Unlike the read-only Console, the assistant panel is **editable** (user can type, send messages, use commands).
- **First impression:** On open, the user sees an ASCII ComfyUI logo, then a short welcome message. This sets the tone and makes the assistant feel like a dedicated “ComfyUI terminal.”

---

## Commands and structure

- **Slash commands (`/`)** — Invoke commands, skills, and tools via a `/` prefix (e.g. `/help`, `/settings`, `/skill-name`). Enables quick access without leaving the chat.
- **Sessions** — Sessions (threads) can be **named** and **recalled**. The user can list, switch, or create named sessions from the UI or via commands.
- **Configuration entry points** — Model selection, API base URL, and API key capture are available from the assistant (e.g. via a first-time setup flow or a settings command).

---

## First-time and configuration flow

- **First run:** The user is guided by a **configuration chat**: the assistant asks a short set of questions (e.g. API provider, model, goals) and the user answers in natural language. Answers are persisted and used for default behaviour.
- **Later:** User can reopen configuration or change SOUL/GOALS via the **`/settings`** command (or equivalent), without leaving the assistant.

---

## Media and attachments (later in Phase 5)

- **Terminal as output:** The “terminal” can **display images** and **play media** (e.g. generated images, previews) inline, so outputs feel part of the same console.
- **Attachments:** The user can **attach files** (images, documents) to messages. The assistant can reference them in replies and tool use (e.g. “use this image for img2img”).

These capabilities are planned as a **second sub-phase** of the Phase 5 UI work (after the core terminal layout, logo, and commands are in place).

---

## Help

- **`/help`** — Shows available commands, a short description of skills and tools, and how to use the assistant (e.g. slash commands, session naming, when to use which tool).

---

## Summary

| Element | Description |
|--------|-------------|
| Layout | Bottom panel (Console-style), editable |
| Look & feel | Terminal/console (Claude Code / Gemini CLI–like), with optional icons |
| On open | ASCII ComfyUI logo + welcome message |
| Commands | `/` for commands, skills, tools; session naming and recovery |
| Config | First-time setup chat; `/settings` for SOUL, GOALS, model, API URL, API key |
| Media | Phase 5 (later): images and media in terminal; attachments on messages |
| Help | `/help` for commands and usage |

This design is implemented in **Phase 5** of the [development phases](comfyui_assistant_development_phases.md).
