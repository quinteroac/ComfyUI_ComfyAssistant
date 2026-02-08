# Installation

This guide covers how to install ComfyUI Assistant as a ComfyUI custom node.

## Prerequisites

- **ComfyUI** installed and working
- **Node.js** (v18 or later recommended) — required for building the frontend
- **npm** — comes with Node.js

## Option 1: Install from ComfyUI Manager (recommended)

If the extension is published in the ComfyUI Manager registry:

1. Open ComfyUI and go to **Manager**.
2. Search for **ComfyUI Assistant** (or the registered name).
3. Click **Install**.
4. Restart ComfyUI.

After installation, the **ComfyUI Assistant** tab appears in the sidebar. If the tab is missing or the UI is blank, the frontend may need to be built manually (see Option 2, step 4).

## Option 2: Manual installation

### 1. Clone into custom_nodes

From your ComfyUI root:

```bash
cd custom_nodes
git clone https://github.com/YOUR_ORG/ComfyUI_ComfyAssistant.git
cd ComfyUI_ComfyAssistant
```

Replace the clone URL with the actual repository URL if different.

### 2. Install frontend dependencies

```bash
cd ui
npm install
```

### 3. Build the frontend

```bash
npm run build
```

The built files are output to `dist/`. **ComfyUI loads the extension from this folder.** Without a successful build, the Assistant tab will not work.

### 4. Restart ComfyUI

Restart ComfyUI so it picks up the new custom node and the built UI.

## Verifying the installation

1. Open ComfyUI in your browser.
2. In the sidebar, you should see a tab named **ComfyUI Assistant** (or as configured in the extension).
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
| No Assistant tab in sidebar | Ensure the extension is in `custom_nodes/ComfyUI_ComfyAssistant` and that you ran `npm run build` inside `ui/`. Restart ComfyUI. |
| Tab is empty or shows errors | Check the browser console (F12). Re-run `cd ui && npm run build` and restart ComfyUI. |
| "Module not found" or build errors | Run `cd ui && npm install` again and then `npm run build`. |
| Assistant does not answer | Configure the API key and (if needed) base URL in `.env` — see [Configuration](configuration.md). |

## Next steps

- [Configuration](configuration.md) — Set up the API and optional onboarding.
- [Base tools](base-tools.md) — What you can ask the assistant to do with your workflow.
