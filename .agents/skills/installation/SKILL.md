---
name: installation
description: Install ComfyUI Assistant as a ComfyUI custom node. Use when performing or troubleshooting installation (clone, Python deps, frontend build, restart).
version: 0.0.1
license: MIT
---

# ComfyUI Assistant — Installation (for agents)

Use this skill when you are asked to **install** or **troubleshoot the installation** of ComfyUI Assistant. It provides the full sequence and key paths so you can run the right commands in the right order.

## When to use

- User asks to install ComfyUI Assistant (manual install)
- User reports "Module not found" or missing Python packages after clone
- User has no Assistant tab or empty tab (frontend not built or wrong path)
- User wants to verify or fix an existing installation

## Prerequisites

| Requirement | Purpose |
|-------------|---------|
| ComfyUI | Host; extension runs inside ComfyUI |
| Python 3.x | Same interpreter as ComfyUI; runs backend |
| Node.js v18+ | Build frontend (Vite) |
| npm | Install frontend deps |

## Installation steps (order matters)

All commands assume ComfyUI root is the starting point unless stated otherwise.

### 1. Clone into custom_nodes

```bash
cd custom_nodes
git clone https://github.com/YOUR_ORG/ComfyUI_ComfyAssistant.git
cd ComfyUI_ComfyAssistant
```

Extension root = `ComfyUI/custom_nodes/ComfyUI_ComfyAssistant/`.

### 2. Install Python dependencies

**From the extension root** (where `pyproject.toml` lives):

```bash
pip install -e .
```

Installs: `openai`, `python-dotenv`, `ddgs`, `beautifulsoup4`. Required for backend (chat, tools, providers). If the user uses a venv for ComfyUI, use that venv’s `pip`.

### 3. Install frontend dependencies

```bash
cd ui
npm install
```

### 4. Build the frontend

```bash
npm run build
```

Output goes to `dist/` (e.g. `dist/example_ext/`). ComfyUI loads the extension from this folder. No build ⇒ no Assistant tab or broken UI.

### 5. Restart ComfyUI

Restart so ComfyUI loads the new node and the built assets.

## Key paths

| Path | Purpose |
|------|---------|
| `pyproject.toml` | Python dependencies (do not edit version bounds without reason) |
| `ui/` | Frontend source; run `npm install` and `npm run build` here |
| `dist/` | Built frontend; must exist for the tab to work |
| `doc/installation.md` | User-facing installation guide |

## Common failures and fixes

| Symptom | Likely cause | Action |
|--------|----------------|--------|
| "Module not found" (Python) | Python deps not installed | From extension root: `pip install -e .` (use ComfyUI’s venv if applicable) |
| No Assistant tab | Extension not in `custom_nodes` or frontend not built | Confirm path `custom_nodes/ComfyUI_ComfyAssistant`, run `cd ui && npm run build`, restart ComfyUI |
| Tab empty or JS errors | Build missing or stale | `cd ui && npm install && npm run build`, restart ComfyUI |
| Assistant does not answer | No provider configured | User must set up a provider in the Assistant tab (or `.env`); see `doc/configuration.md` |

## User docs

- Full install guide: `doc/installation.md`
- Configuration (API, providers): `doc/configuration.md`
