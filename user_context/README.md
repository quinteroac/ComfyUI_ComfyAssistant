# User context workspace (Phase 1)

This folder is the assistant’s **writable workspace**. The backend creates it on first use (onboarding or first chat). Do not commit personal local data in `context.db`, `goals.md`, `personas/`, or the contents of `skills/` (they are in `.gitignore`).

## Layout

| Path | Purpose |
|------|---------|
| `context.db` | SQLite: user rules, preferences, onboarding flag |
| `SOUL.md` | Legacy fallback personality file (kept for backward compatibility) |
| `goals.md` | User goals and experience level |
| `personas/<persona-slug>/SOUL.md` | Persona-specific personality file with frontmatter (`Name`, `Description`, `Provider`) and free-text body |
| `skills/<skill-name>/SKILL.md` | One directory per user skill (Agent Skills standard) |

## Personas format

Personas use one folder per persona:

- `user_context/personas/<persona-slug>/SOUL.md`

`SOUL.md` must contain YAML frontmatter plus body text:

```markdown
---
Name: Persona display name
Description: What this persona is for
Provider: configured-provider-name
---

Free-text personality instructions.
```

The backend loads the persona file when `preferences.active_persona` is set in `context.db` and the `Provider` matches a configured provider.

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
