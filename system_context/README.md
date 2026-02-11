# System context

This directory holds the **base system prompt** for the ComfyUI Assistant. Load order: (1) top-level `.md` files in sorted order, (2) `skills/<name>/SKILL.md` per skill directory (sorted by directory name). `README.md` is skipped.

The full context injected into the LLM is:

**system_context** (this directory + skills) **+ user_context** (rules, SOUL, goals, skills from `user_context/`).

## Skills format (Agent Skills standard)

Skills follow the [Agent Skills](https://agentskills.io) standard (see [Claude Code skills](https://code.claude.com/docs/en/skills)). Each skill is a **directory** with a **SKILL.md** file:

- **SKILL.md** has YAML frontmatter (between `---` markers) then markdown body. The body is what gets injected into the prompt.
- **Frontmatter**: `name` (skill identifier), `description` (when to use it; helps the agent know what the skill does).

```
skills/
├── 01_base_tools/
│   └── SKILL.md
├── 02_tool_guidelines/
│   └── SKILL.md
└── 03_node_reference/
    └── SKILL.md
```

Example **SKILL.md**:

```yaml
---
name: base-tools
description: Base graph tools (addNode, removeNode, connectNodes, getWorkflowInfo). Use when modifying workflows.
---

# Base tools (always available)
...
```

## Layout

| Path | Purpose |
|------|---------|
| `01_role.md` | Role, base vs user skills note, language, formatting, communication style, important guidelines |
| `skills/01_base_tools/SKILL.md` | Base tools, when to use, best practices |
| `skills/02_tool_guidelines/SKILL.md` | Tool usage guidelines |
| `skills/03_node_reference/SKILL.md` | Common node types and workflow reference |
| `skills/07_workflow_guardrails/SKILL.md` | Decision order and safety checks for workflow requests |
| `skills/08_comfyui_examples_source/SKILL.md` | Use ComfyUI_examples as the first source for workflows |
| `skills/09_model_flux/SKILL.md` | Flux workflows from ComfyUI_examples |
| `skills/10_model_flux2/SKILL.md` | Flux2 workflows from ComfyUI_examples |
| `skills/11_model_lumina2/SKILL.md` | Lumina2 workflows from ComfyUI_examples |
| `skills/12_model_qwen_image/SKILL.md` | Qwen Image workflows from ComfyUI_examples |
| `skills/13_model_sdxl/SKILL.md` | SDXL workflows from ComfyUI_examples |
| `skills/14_model_wan/SKILL.md` | WAN workflows from ComfyUI_examples |
| `skills/15_model_wan22/SKILL.md` | WAN 2.2 workflows from ComfyUI_examples |
| `skills/16_model_z_image/SKILL.md` | Z-Image workflows from ComfyUI_examples |
| `skills/17_model_loading_rules/SKILL.md` | Rules for UNETLoader vs CheckpointLoader selection |

To add a base skill: create a new directory under `skills/` (use a numeric prefix to control order) and add `SKILL.md` with frontmatter and body.

## Loading

The backend loads via `user_context_loader.load_system_context(system_context_path)`. If the directory is missing or empty, a minimal fallback prompt is used so the assistant still works.
