---
name: ralph-orchestrator
description: "Orchestrate Ralph autonomous agent execution. Reads prd.json, spawns sub-agents sequentially for each user story, validates via progress.txt. Use when: run ralph, execute prd, orchestrate ralph, run all user stories, execute prd.json."
user-invocable: true
---

# Ralph Orchestrator

Orchestrates the execution of a Ralph PRD by spawning sub-agents for each user story sequentially. Each sub-agent implements one story; the orchestrator validates and proceeds to the next until all pass.

---

## Prerequisites

- **PRD file**: `.project/planning/.ralph/prd.json`
- **Sub-agent prompt**: `.project/planning/.ralph/prompt.md`
- **Status log**: `.project/planning/.ralph/progress.txt` (created/updated by sub-agents)

---

## Orchestration Workflow

### Step 1: Load PRD

Read `.project/planning/.ralph/prd.json`.

Extract:
- `userStories` array
- For each story: `id`, `title`, `priority`, `passes`

### Step 2: Determine Pending Stories

Filter stories where `passes === false`.

Sort by `priority` ascending (lowest number = first).

### Step 3: Read Current Status

Read `.project/planning/.ralph/progress.txt` if it exists.

- Use the `## Codebase Patterns` section for context before each sub-agent run
- Use the latest entries to understand what has been done and any learnings

### Step 4: Loop Over Pending Stories (Sequential)

For each pending story in order:

#### 4.1 Launch Sub-Agent

**Spawn a new agent/Composer session** with:

1. **System instructions**: The full content of `.project/planning/.ralph/prompt.md`
2. **Context**: The current story (id, title, description, acceptanceCriteria)
3. **Focus**: "Implement only story [ID]: [Title]. Do not work on other stories."

**How to spawn (depending on environment):**

- **Cursor**: Open a new Composer tab; paste the prompt.md content plus: "Focus on implementing US-XXX: [Title]. The PRD is at .project/planning/.ralph/prd.json."
- **Amp / CLI**: If you have `ralph.sh` or equivalent, run it; it will spawn an instance with the prompt
- **Other**: Use whatever mechanism spawns a fresh agent with the Ralph prompt

#### 4.2 Wait for Completion

**Do not proceed until the sub-agent has finished.**

- The sub-agent commits, updates prd.json (`passes: true`), and appends to progress.txt
- If the user triggers sub-agents manually: wait for the user to confirm "sub-agent finished" or "story US-XXX done"
- If automated: poll or await the sub-agent process exit

#### 4.3 Validate

After the sub-agent reports done:

1. **Read** `.project/planning/.ralph/prd.json` — confirm the story now has `passes: true`
2. **Read** `.project/planning/.ralph/progress.txt` — confirm a new entry for this story
3. If validation fails: report the issue; optionally retry once or ask the user to fix

#### 4.4 Next Story

If validation passes, continue to the next pending story.

### Step 5: Completion

When all stories have `passes: true`:

- Report: "All user stories complete. Ralph execution finished."
- Optionally summarize what was implemented from progress.txt

---

## Status Tracking

**progress.txt** is the source of truth for sub-agent activity:

- Sub-agents append entries; never overwrite
- Each entry includes: date/time, story ID, what was implemented, files changed, learnings
- The `## Codebase Patterns` section at the top consolidates reusable patterns

**To check status:**

1. Read `progress.txt` to see which stories have been completed and any patterns
2. Read `prd.json` to see which stories have `passes: true`

---

## Checklist for Orchestrator

Before starting:
- [ ] Read prd.json
- [ ] Read progress.txt (if exists)
- [ ] List pending stories by priority

For each story:
- [ ] Launch sub-agent with prompt.md + story focus
- [ ] Wait for sub-agent completion
- [ ] Validate: prd.json shows passes: true for this story
- [ ] Validate: progress.txt has new entry
- [ ] Proceed to next story only after validation

---

## Handoff Template (Manual Sub-Agent)

When the user must spawn the sub-agent manually, output:

```
## Sub-Agent Instructions

1. Open a new Composer / Agent session
2. Load the Ralph prompt: .project/planning/.ralph/prompt.md
3. Add this focus:

   Implement ONLY story [US-XXX]: [Title]
   - Description: [description]
   - Acceptance criteria: [list]
   - PRD path: .project/planning/.ralph/prd.json
   - Progress log: .project/planning/.ralph/progress.txt

4. Let the sub-agent run until it commits and updates prd.json
5. Return here and say "US-XXX done" so I can validate and continue
```

---

## Important

- **Sequential only**: One story at a time. Do not spawn parallel sub-agents.
- **Validate before proceeding**: Always confirm prd.json and progress.txt before the next story.
- **One story per sub-agent**: Each sub-agent works on a single user story; the Ralph prompt instructs it to pick the highest-priority pending story, so providing explicit story focus ensures correct targeting.
