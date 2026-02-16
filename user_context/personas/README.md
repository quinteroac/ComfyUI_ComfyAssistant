# Personas workspace

Each persona must be stored in its own folder:

`user_context/personas/<persona-slug>/SOUL.md`

Rules:

- `<persona-slug>` must be a valid slug (recommended kebab-case).
- Each persona folder must contain exactly one `SOUL.md`.
- `SOUL.md` must start with YAML frontmatter containing:
  - `Name`
  - `Description`
  - `Provider` (must match a configured provider name in `providers.db`)
- After frontmatter, include free-text personality instructions.

Example:

```markdown
---
Name: Creative Director
Description: Cinematic visual storyteller for concept workflows
Provider: openai-main
---

You are a cinematic creative director. Speak in concise actionable steps, and
prioritize composition, lighting, and mood consistency in workflow suggestions.
```
