# User skills

User **skills** are custom instructions you give to the assistant. They are stored as files in `user_context/skills/` and are read by the backend and injected into the system prompt. The assistant uses them when replying and when using tools (e.g. when building or modifying workflows).

## What skills are for

- **Preferences**: e.g. "Always use Preview Image instead of Save Image."
- **Workflow habits**: e.g. "When adding a KSampler, set steps to 20 by default."
- **Domain rules**: e.g. "When the user asks for a portrait, suggest 512×768 resolution."

Skills are **manual** in the current version: you create and edit the files yourself. The assistant does not create or delete skill files (that will be possible in a future phase with a `create_skill` tool).

## Where skills live

- **Directory**: `user_context/skills/`
- **One skill per directory**: each skill has its own folder with a `SKILL.md` file inside.

Example:

```
user_context/skills/
├── preview-instead-of-save/
│   └── SKILL.md
├── default-sampler-steps/
│   └── SKILL.md
└── dummy-test/
    └── SKILL.md
```

The folder name is the **skill name** (e.g. `preview-instead-of-save`). The assistant only sees skills that exist in this folder and that are loaded into the user context block.

## Skill format (SKILL.md)

Skills follow the [Agent Skills](https://agentskills.io) standard. Each `SKILL.md` has:

1. **YAML frontmatter** between `---` lines: `name` and `description`.
2. **Markdown body**: instructions for the assistant.

### Frontmatter

- **name**: Identifier of the skill (lowercase, hyphens allowed). Usually matches the folder name.
- **description**: Short explanation of what the skill does and when the assistant should use it.

### Body

Plain markdown: headings, lists, paragraphs. This is the actual instruction set the assistant will follow when the skill is applied.

### Example: Preview instead of Save

**File:** `user_context/skills/preview-instead-of-save/SKILL.md`

```yaml
---
name: preview-instead-of-save
description: Use Preview Image instead of Save Image when saving output. Apply when the user or workflow would add Save Image.
---

# Always use Preview Image instead of Save Image

When the user or the workflow would add or use Save Image, use Preview Image instead so they can preview in the UI and download manually.
```

### Example: Default sampler steps

**File:** `user_context/skills/default-sampler-steps/SKILL.md`

```yaml
---
name: default-sampler-steps
description: When adding a KSampler, set steps to 20 and cfg to 7 unless the user specifies otherwise.
---

# Default KSampler settings

After adding a KSampler node:
- Set **steps** to 20 if the user did not ask for a different value.
- Set **cfg** to 7 if not specified.
```

## Legacy format (flat file)

Older style is still supported: a single file per skill **without** a subfolder:

- **Path**: `user_context/skills/<slug>.md` (e.g. `preview-instead-of-save.md`)
- **Slug**: Filename without `.md`.

These files are loaded and the filename (without extension) is used as the skill identifier. For new skills, prefer the **directory + SKILL.md** format with frontmatter.

## How the assistant uses skills

- Skills are loaded by the backend and included in the **User context** block of the system message.
- The assistant is instructed to use **only** the skills listed in that block.
- When your message is about workflows or preferences, the model can apply the relevant skill (e.g. use Preview Image instead of Save Image, or set default steps).

You do not need to "invoke" a skill by name in the chat; the assistant decides when a skill applies based on its `description` and the conversation.

## Adding or editing a skill

1. Create a folder under `user_context/skills/` with a short name (e.g. `preview-instead-of-save`).
2. Create `SKILL.md` inside that folder.
3. Add the YAML frontmatter (`name`, `description`) and the markdown instructions.
4. Save the file. The next time you send a message, the backend will load the updated skills (no need to restart ComfyUI for content changes in `user_context/`).

To **remove** a skill, delete its folder (or the `.md` file in the legacy format).

## Tips

- **Keep descriptions clear**: The `description` helps the assistant decide when to use the skill.
- **One concern per skill**: Easier to maintain and to enable/disable (by removing the folder).
- **Use the same language as your chat**: If you speak to the assistant in Spanish, skills in Spanish work well; the same for English.

## Next steps

- [Base tools](base-tools.md) — What the assistant can do in the canvas and how to ask in natural language.
