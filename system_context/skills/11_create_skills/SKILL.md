---
name: 'Create Skills'
description: 'When the user asks to create or design a skill, follow a clear process: clarify intent, draft name/description/instructions, then call createSkill. Optionally offer to create a skill when you automate a procedure they might want to reuse.'
---

# Creating user skills

When the user wants to **create a new skill** (e.g. "create a skill that...", "I want a skill for...", "remember to always...", or "make a skill so that..."), follow this process.

## 1. Clarify what they want

- If the request is vague, ask one short question: what should the skill do, or in what situation should it apply.
- If they gave a clear procedure or preference, skip to step 2.

## 2. Draft the skill

Prepare three pieces before calling **createSkill**:

| Field | Purpose | Guidelines |
|-------|---------|------------|
| **name** | Short label (shown in lists) | 2–6 words; descriptive. Example: "Use Preview Image", "Organize workflow after apply". |
| **description** | One sentence for the system | What the skill does or when it applies. Used in context so the assistant knows when to use it. |
| **instructions** | Full body of the skill | Clear, actionable steps. Use numbered lists for procedures. Say what to do and what to avoid. |

**Instructions best practices:**

- Write in imperative form: "Call getWorkflowInfo with fullFormat: true", "Do not ask the user for confirmation".
- For procedures: ordered steps (1, 2, 3…) and optional sub-bullets.
- Include triggers: "When the user asks to organize a workflow…", "When adding a sampler node…".
- Add guardrails when relevant: "Do not…", "Always…", "If X, then Y".
- Keep it one skill = one concern; if they asked for two different things, offer two skills or ask which to implement first.

## 3. Call createSkill

- Invoke **createSkill** with the `name`, `description`, and `instructions` you drafted.
- If the backend returns an error (e.g. skill already exists), suggest a different name or use **updateSkill** if they want to replace an existing skill.

## 4. Confirm and offer to tune

- After creating, briefly confirm: name, what it does, and that it will be used in future conversations.
- Offer to adjust: "If you want to change the wording or add steps, say so and I can update that skill (use updateSkill with the slug)."

## When to suggest creating a skill

- After you automate a multi-step procedure they might repeat (e.g. "organize workflow", "add my usual upscale chain").
- When they say "remember that", "from now on", "always do X", "I prefer Y".
- When they ask "can you do X every time?" — implement it and offer to save it as a skill.

Do not create a skill without the user having expressed a desire to remember something or to have a reusable procedure. If in doubt, offer: "Do you want me to save this as a skill so I do it automatically next time?"
