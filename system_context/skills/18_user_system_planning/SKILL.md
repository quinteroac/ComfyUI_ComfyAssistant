---
name: user-system-planning
description: For complex user requests — evaluate, investigate, ask questions, propose a plan, accept modifications, then execute. Use when the request is multi-step, ambiguous, or high-impact.
---

# User-System Planning (complex requests)

When the user's request is **complex**, follow this planning workflow instead of acting immediately. This ensures clarity, avoids wrong assumptions, and lets the user approve or adjust the plan before execution.

## When to use this workflow

Treat the request as **complex** when any of the following apply:

- **Multi-step**: Requires several tools or actions in sequence (e.g. "set up a full pipeline with ControlNet and upscale").
- **Ambiguous**: Goal or constraints are unclear (e.g. "make it better", "add something for quality").
- **High-impact**: Would change many nodes, replace the whole workflow, or affect models/skills (e.g. "rebuild my workflow for Flux").
- **Research-heavy**: You are not confident about nodes, models, or workflows and need to look things up first.
- **User asks for a plan**: User says "plan it first", "what would you do?", "outline the steps", or similar.

For **simple** requests (single clear action, e.g. "add a KSampler", "set steps to 30"), proceed directly with the appropriate tools; do not force a full plan.

---

## Planning workflow (6 steps)

### 1. Evaluate the request

- Summarize in your own words what the user wants and what "done" looks like.
- Identify unknowns: missing info (models, resolution, style), conflicting goals, or technical uncertainty.
- Decide if you have enough to draft a plan or if you must gather more information first.

### 2. Investigate (before proposing a plan)

Gather what you need so the plan is grounded and executable:

| What to check | How |
|---------------|-----|
| **Skills** | `listUserSkills`, `listSystemSkills`; use `getUserSkill` / `getSystemSkill` when a skill might apply. |
| **Environment** | `getWorkflowInfo` (current canvas), `searchInstalledNodes`, `getAvailableModels`; use `refreshEnvironment` if the user may have just installed something. |
| **Workflows / templates** | `searchTemplates`, `getExampleWorkflow`; consider workflow-guardrails order (templates → examples → web). |
| **External / docs** | `webSearch`, `fetchWebContent`, `readDocumentation`, `searchNodeRegistry` when you need tutorials, node docs, or packages. |

Do only the investigation that is needed for this request. Avoid unnecessary tool calls.

### 3. Ask the user when needed

Ask **before** locking in a plan when:

- Goals or priorities are unclear (e.g. speed vs quality, which model family).
- Choices affect the plan (e.g. "Do you want to keep your current nodes or start from a template?").
- Required info is missing (e.g. resolution, style, or which checkpoint to use).
- You found several valid approaches and the user should choose (e.g. "I found template A and B; which do you prefer?").

Keep questions short and concrete. One message can contain multiple questions.

### 4. Propose a plan

Present a clear, numbered plan to the user:

- **Objective**: One sentence on what will be achieved.
- **Steps**: Numbered list of concrete actions (which tools or changes you will make, in order).
- **Assumptions**: What you assumed (e.g. "using your current checkpoint", "replacing the current workflow").
- **Alternatives** (optional): Brief note if there was another reasonable option (e.g. "Alternatively we could use a template instead of building from scratch").

Ask explicitly for approval or changes, e.g.: "If this looks good, say so and I’ll execute it; or tell me what to change."

### 5. Accept modifications and adjust

- If the user asks for changes (add/remove/reorder steps, different models, different approach), update the plan and show the revised version.
- Confirm again: "Here’s the updated plan. Say when to proceed or what else to change."
- Repeat until the user is satisfied or explicitly asks you to execute.

### 6. Execute the plan

- Only after the user **clearly accepts** (e.g. "yes", "go ahead", "do it", "execute"), run the plan step by step.
- Use the appropriate tools in the order you described; explain briefly what you’re doing as you go.
- If something fails mid-execution (e.g. tool error, missing model), stop, report the issue, and suggest a small revised plan or ask the user how to proceed.

---

## Summary

| Step | Action |
|------|--------|
| 1 | Evaluate: summarize goal, list unknowns. |
| 2 | Investigate: skills, environment, workflows, web/docs as needed. |
| 3 | Ask the user when goals, choices, or missing info would change the plan. |
| 4 | Propose a numbered plan and ask for approval or changes. |
| 5 | Incorporate feedback and re-present the plan until the user is satisfied. |
| 6 | Execute only after explicit acceptance; on failure, report and adjust. |

Keep plans concise and actionable. Do not invent steps you cannot perform with your tools; if you need the user to do something (e.g. install a node, download a model), say so in the plan.
