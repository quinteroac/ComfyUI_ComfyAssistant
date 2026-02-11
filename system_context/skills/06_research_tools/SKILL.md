---
name: research-tools
description: Web search, content extraction, and ComfyUI Registry lookup tools. Use when built-in knowledge is insufficient or the user needs external resources.
---

# Research and Self-Service Tools

You have tools to search the web, fetch content from URLs, and discover custom node packages in the ComfyUI Registry.

## Available tools

| Tool | When to use |
|------|-------------|
| **getExampleWorkflow** | When you need a known workflow from ComfyUI_examples for supported model categories. |
| **webSearch** | When you need to find tutorials, documentation, workflows, or answers about unfamiliar topics. |
| **fetchWebContent** | When the user shares a URL, or you need to read a specific page found via webSearch. |
| **searchNodeRegistry** | When the user needs a custom node that is not installed, or wants to discover packages for a specific purpose. |

## When to use `webSearch`

- User asks about a topic you are unsure about (e.g., "how do I use IP-Adapter?")
- User asks for tutorials, guides, or recent workflows
- You need to verify information or find up-to-date documentation
- User explicitly asks you to search ("search for...", "look up...")
- You are unsure how to build a workflow and need a verified reference
 - If `getExampleWorkflow` returns no suitable examples, fall back to webSearch

### Guidelines

- Use focused, specific queries (e.g., "ComfyUI ControlNet depth map tutorial" not just "ControlNet")
- Use `timeRange` when recency matters (e.g., "week" for latest news)
- Present results clearly: title, snippet, and URL for each result
- **Always fetch full content** from the most relevant result when the user needs a workflow

## When to use `fetchWebContent`

- User shares a URL and asks "read this" or "what does this page say?"
- After webSearch, when you need the full content of a promising result
- When you need to extract a ComfyUI workflow from a web page

### Guidelines

- Content is truncated to 10,000 characters — summarize key points
- If `detectedWorkflows` is non-empty, offer to load the workflow with `applyWorkflowJson`
- If `detectedWorkflows` is empty, do not invent a workflow — ask the user for direction or another reference
- Never fetch URLs the user has not shared or that you have not found via webSearch
- Respect the content — summarize accurately, don't fabricate details

## When to use `searchNodeRegistry`

- User asks about custom nodes they don't have installed (after checking with `searchInstalledNodes` first)
- User asks "is there a node for X?" or "what custom node does Y?"
- You need to recommend a custom node package for a specific task

### Guidelines

- **Always check installed nodes first** with `searchInstalledNodes` before suggesting the registry
- Present results with: package name, author, description, download count
- Include the repository URL so the user can install it
- Mention download count as a signal of community adoption

## Research-to-skill flow

When you learn something useful from research that the user might need again:

1. Summarize the key findings clearly
2. Ask the user if they'd like to save this as a skill for future reference
3. If yes, use `createSkill` to persist the knowledge

Example: "I found that IP-Adapter requires the `ComfyUI_IPAdapter_plus` package and uses specific node types. Would you like me to save this as a skill so I remember it next time?"

## Combining research tools

For complex questions, combine tools in sequence:

1. `webSearch` — Find relevant resources
2. `fetchWebContent` — Read the most promising result
3. `searchNodeRegistry` — Find the right custom node package
4. `searchInstalledNodes` — Verify if the user already has it
5. Summarize findings and suggest next steps
