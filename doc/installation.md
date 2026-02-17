# Installation

This guide covers how to install ComfyUI Assistant as a ComfyUI custom node.

## Prerequisites

- **ComfyUI** installed and working
- **Python 3.x** (same as ComfyUI) — for backend and Python dependencies
- **Node.js** (v18 or later recommended) — required for building the frontend
- **npm** — comes with Node.js

The extension is **not yet in the ComfyUI Manager registry**. Install manually as below. Once it is published, you will be able to install it from Manager → search for "ComfyUI Assistant".

## Manual installation

### 1. Clone into custom_nodes

From your ComfyUI root:

```bash
cd custom_nodes
git clone https://github.com/YOUR_ORG/ComfyUI_ComfyAssistant.git
cd ComfyUI_ComfyAssistant
```

Replace the clone URL with the actual repository URL if different.

### 2. Install Python dependencies

From the extension root (where `pyproject.toml` is):

```bash
pip install -r requirements.txt
```

This installs the backend dependencies (`openai`, `python-dotenv`, `ddgs`, `beautifulsoup4`). Without this step, the assistant backend may fail with "Module not found" when handling chat or tools.

### 3. Install frontend dependencies

```bash
cd ui
npm install
```

### 4. Build the frontend

```bash
npm run build
```

The built files are output to `dist/` (assets under `dist/example_ext/`). **ComfyUI loads the extension from this folder.** Without a successful build, the Assistant tab will not work.

### 5. Restart ComfyUI

Restart ComfyUI so it picks up the new custom node and the built UI.

## Using an AI agent to install

You can have **Claude**, **Codex**, **Cursor**, or another AI agent perform the installation for you. The agent can run the commands in order and fix common issues if something fails.

### How to do it

1. **Open the project in the agent’s environment**  
   Open the ComfyUI repo (or at least the `custom_nodes/ComfyUI_ComfyAssistant` folder) in the tool where the agent runs (e.g. Cursor workspace, Codex workspace).

2. **Give the agent the installation context**  
   Tell the agent to use the installation skill so it has the full steps and paths. For example:
   - *“Install ComfyUI Assistant following the instructions in `.agents/skills/installation/SKILL.md`”*
   - *“Follow doc/installation.md and run the installation steps for me”*

3. **Let the agent run the steps**  
   The agent will run: clone (if needed), `pip install -r requirements.txt`, `cd ui && npm install && npm run build`, and remind you to restart ComfyUI. If you use a Python venv for ComfyUI, say so so it uses the same `pip`.

4. **If something fails**  
   Ask the agent to fix it and point it again at the skill or at this guide; the skill includes a troubleshooting table (e.g. “Module not found”, missing tab, empty tab).

### Agent skill (for the agent)

- **Skill path:** [.agents/skills/installation/SKILL.md](../.agents/skills/installation/SKILL.md)  
  Prerequisites, step-by-step commands, key paths, and common failures. Use this so the agent does not skip Python deps or the frontend build.

## Verifying the installation

1. Open ComfyUI in your browser.
2. In the bottom panel, you should see a tab named **ComfyUI Assistant** (or as configured in the extension).
3. Open that tab. You should see the chat interface.
4. Before the assistant can reply, you must configure the API (see [Configuration](configuration.md)).

## Development: watch mode

If you are developing or modifying the frontend:

```bash
cd ui
npm run watch
```

With `watch` running, source changes are rebuilt automatically. Refresh the browser to see updates. Normal users only need `npm run build` once after install.

## Troubleshooting

| Problem | What to try |
|--------|--------------|
| No Assistant tab in bottom panel | Ensure the extension is in `custom_nodes/ComfyUI_ComfyAssistant` and that you ran `npm run build` inside `ui/`. Restart ComfyUI. |
| Tab is empty or shows errors | Check the browser console (F12). Re-run `cd ui && npm run build` and restart ComfyUI. |
| "Module not found" (Python) | From the extension root run `pip install -r requirements.txt` (use ComfyUI’s venv if you use one). |
| "Module not found" or build errors (frontend) | Run `cd ui && npm install` again and then `npm run build`. |
| Assistant does not answer | Configure a provider via the **Provider Wizard** in the Assistant tab (or `/provider-settings`). Optional: use `.env` fallback — see [Configuration](configuration.md). |

## Next steps

- [Configuration](configuration.md) — Set up the API and optional onboarding.
- [Base tools](base-tools.md) — What you can ask the assistant to do with your workflow.
