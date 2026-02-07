# User context workspace (Phase 1)

This folder is the assistant’s **writable workspace**. The backend creates it on first use (onboarding or first chat). Do not commit `context.db`, `SOUL.md`, `goals.md`, or the contents of `skills/` (they are in `.gitignore`).

## Layout

| Path | Purpose |
|------|---------|
| `context.db` | SQLite: user rules, preferences, onboarding flag |
| `SOUL.md` | Personality / tone (from onboarding or manual edit) |
| `goals.md` | User goals and experience level |
| `skills/<skill-name>/SKILL.md` | One directory per user skill (Agent Skills standard) |

## Skills format (Agent Skills standard)

User skills follow the [Agent Skills](https://agentskills.io) standard (see [Claude Code skills](https://code.claude.com/docs/en/skills)). Each skill is a **directory** with a **SKILL.md** file:

- **SKILL.md** has YAML frontmatter between `---` markers, then markdown instructions.
- **Frontmatter**: `name` (skill identifier, lowercase with hyphens), `description` (what the skill does and when to use it).

**Example** — `skills/preview-instead-of-save/SKILL.md`:

```yaml
---
name: preview-instead-of-save
description: Use Preview Image instead of Save Image when saving output. Apply when the user or workflow would add Save Image.
---

# Always use Preview Image instead of Save Image

When the user or the workflow would add or use Save Image, use Preview Image instead so they can preview in the UI and download manually.
```

**Legacy:** Flat files `skills/<slug>.md` (no directory, no frontmatter) are still loaded; the filename (without `.md`) is used as the slug. Prefer the directory + SKILL.md format for new skills.

The assistant reads these skills and applies them when creating or modifying workflows. In Phase 3, the agent will be able to create skills via the `create_skill` tool; until then, add or edit them by hand.

## More

See `.agents/project-context.md` in the repo for full implementation details.
