# PRD: Agent Personas System

## 1. Introduction / Overview

ComfyUI Assistant must support **personas**: personality schemas that the user can define so the agent adopts different styles (creative, technical, specialized, or playful) depending on the goal. Each persona is tied to a specific **provider** and **model**, so the underlying model fits the personality (e.g. some personas work better with frontier models, others with more entertainment-oriented ones). This PRD specifies the data structure, assisted creation flow, in-conversation usage, and persona deletion.

## 2. Goals

- Allow defining multiple agent personalities (personas) with name, description, and associated provider.
- Store each persona in a `SOUL.md` file under `user_context/personas/[persona_name]/`.
- Provide a guided flow (system skill) to create personas by asking the user questions.
- Allow switching persona in conversation with `/persona [persona_name]`, with access to history.
- Allow deleting a persona with `/persona del [persona_name]`.

## 3. User Stories

### US-001: Folder structure and SOUL.md per persona
**Description:** As a developer, I need each persona to have its own folder and a SOUL.md file with YAML frontmatter and body text so the system can load and apply the personality.

**Acceptance Criteria:**
- [ ] Each persona lives under `user_context/personas/[persona_name]/` (name in kebab-case or valid slug).
- [ ] There is exactly one `SOUL.md` file per persona in that folder.
- [ ] SOUL.md has YAML frontmatter with: `Name`, `Description`, `Provider` (a previously configured provider).
- [ ] After the frontmatter, the file body describes the personality in free text.
- [ ] Typecheck/lint passes.

### US-002: System skill to create personas (conversational assistant)
**Description:** As a user, I want an assistant that guides me with questions to create a persona, so I don't have to edit files by hand.

**Acceptance Criteria:**
- [ ] There is an invocable system skill (e.g. "create persona" / "I want to create a persona") that starts the flow.
- [ ] The assistant asks: "What will be the name of the persona?" and waits for a response.
- [ ] The assistant asks: "Can you describe the personality? (behavior, background, specialty…)" and waits for a response.
- [ ] The assistant shows a list of configured providers (via `providers list` or equivalent) and asks which provider will represent the persona.
- [ ] After the user chooses a provider, the assistant creates the folder and `SOUL.md` in the defined format and confirms creation to the user.
- [ ] Typecheck/lint passes.

### US-003: Slash command to switch persona in conversation
**Description:** As a user, I want to use `/persona [persona_name]` during a conversation to switch to that persona, keeping the history.

**Acceptance Criteria:**
- [ ] The command `/persona [persona_name]` is registered and recognized by the system.
- [ ] When executed, the agent switches to the provider/model and SOUL.md of the indicated persona.
- [ ] The persona has access to the current conversation history (if any).
- [ ] If `[persona_name]` does not exist, a clear error message is shown (and optionally the list of available personas).
- [ ] Typecheck/lint passes.
- [ ] **[UI]** Verify in browser with dev-browser skill that the command is reflected in the UI (selector or active persona indicator, if applicable).

### US-004: Command to delete a persona
**Description:** As a user, I want to delete a persona with `/persona del [persona_name]` to remove its definition from the system.

**Acceptance Criteria:**
- [ ] The command `/persona del [persona_name]` is registered and recognized.
- [ ] When executed, the folder `user_context/personas/[persona_name]/` and its contents (including SOUL.md) are removed.
- [ ] If that persona was in use, the system falls back to a default persona or indicates that another must be chosen.
- [ ] If `[persona_name]` does not exist, a clear error message is shown.
- [ ] Typecheck/lint passes.

### US-005: List available personas (optional for MVP)
**Description:** As a user, I want to see which personas I have defined so I can choose one or check names before using `/persona` or `/persona del`.

**Acceptance Criteria:**
- [ ] There is a way to list personas (e.g. `/persona` with no arguments, or "list personas", per design).
- [ ] The list shows at least each persona's name (and optionally a short description).
- [ ] Typecheck/lint passes.
- [ ] **[UI]** Verify in browser with dev-browser skill if the list is shown in the UI.

## 4. Functional Requirements

- **FR-1:** The system must store each persona in `user_context/personas/[persona_name]/SOUL.md` with YAML frontmatter (`Name`, `Description`, `Provider`) and body text.
- **FR-2:** The system must provide a system skill that, by asking the user (name, personality description, provider choice), creates the folder and SOUL.md and confirms creation.
- **FR-3:** The system must obtain the list of configured providers (e.g. via `providers list`) to show in the creation flow.
- **FR-4:** The system must interpret the command `/persona [persona_name]` and switch the agent to that persona, applying its SOUL and provider/model, with access to conversation history.
- **FR-5:** The system must interpret the command `/persona del [persona_name]` and remove that persona's folder and SOUL.md.
- **FR-6:** When switching or deleting persona, the system must handle the "persona does not exist" case with a clear error message.

## 5. Non-Goals (Out of Scope)

- This PRD does not require a graphical persona selector in the UI (may be added in a later phase).
- The exact format of "providers list" is not defined here (assumed to exist or integrate with the existing providers module).
- No versioning or automatic backup of SOUL.md on delete.
- No in-assistant editing of a persona (creation and deletion only); editing can be done by manually editing SOUL.md in a first version.

## 6. Design Considerations

- **UX:** The creation flow must be conversational and clear; questions should follow a logical order (name → personality → provider).
- **Consistency:** Persona names should be normalized to a slug (kebab-case, no spaces) for folder names and for the `/persona [persona_name]` command.
- **Reuse:** Leverage the existing providers system for listing and provider↔persona association.

## 7. Technical Considerations

- **Base path:** `user_context/personas/` must exist or be created; define whether `user_context` is relative to the node or to ComfyUI (see project conventions).
- **Integration:** The runtime that runs the agent must be able to switch provider/model and "system prompt" (SOUL.md content) when switching persona.
- **Security:** Validate and sanitize `persona_name` to avoid path traversal (e.g. disallow `..` and characters not allowed in slugs).
- **Persistence:** "Active persona" state may be stored in the thread or in user preferences, per current assistant-ui architecture.

## 8. Success Metrics

- A user can create a full persona in under 2 minutes using the assistant.
- Switching persona with `/persona [persona_name]` takes effect on the next agent response.
- No path or provider errors when using valid persona names; clear errors when the name does not exist or is invalid.

## 9. Open Questions

- Should `/persona` with no arguments list personas, show the current persona, or both? show the current persona
- Should confirmation be required before running `/persona del [persona_name]`? No confirmation required, as the user is capturing the name of the persona no intentional delete is not expected.
- Where is `user_context` (absolute/relative path) defined in the ComfyUI Assistant project? Is defined, read .agents/ docs to know how is the assistant directory structure
- Is the default persona (when opening a new conversation) fixed per installation or configurable per user?  When the assistant is configured by the first time, a SOUL.md is created with the "default" personality,
  in new conversations this will be the one loaded.
