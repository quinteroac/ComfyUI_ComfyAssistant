# Quick Start Guide - ComfyUI Assistant

Get the AI Assistant running in your ComfyUI workflow in minutes.

---

## Prerequisites

1.  **AI Provider API Key:**
    Create a `.env` file in the root directory (copy from `.env.example`):
    ```bash
    # For OpenAI-compatible providers (Groq, Together, OpenAI, etc.)
    OPENAI_API_KEY=your_api_key_here
    OPENAI_API_BASE_URL=https://api.openai.com/v1
    OPENAI_MODEL=gpt-4o
    
    # OR for Google Gemini (via gemini-cli)
    # Ensure you have gemini-cli installed and authenticated
    LLM_PROVIDER=gemini_cli
    ```

2.  **Frontend built:**
    If you installed manually, ensures the UI is compiled:
    ```bash
    cd ui
    npm install
    npm run build
    ```

---

## Start Using

### 1. Launch ComfyUI
Restart your ComfyUI server to load the extension.

### 2. Open the Assistant
- Locate the **ComfyUI Assistant** tab in the bottom panel (next to the Console/Queue tabs).
- Click to open the chat interface.

### 3. Basic Workflow Commands
Try these natural language commands to interact with your graph:

- `"Add a KSampler and a Checkpoint Loader"`
- `"Create a basic SDXL text-to-image workflow"`
- `"Connect the VAE output of the loader to the VAE input of the decode node"`
- `"Set the steps to 25 and CFG to 7.5 on the sampler"`

### 4. Apply Complete Workflows (by model)
The assistant can load **full workflows** in one go instead of adding nodes one by one:

- `"Load the official SDXL workflow"`
- `"I want a Flux dev text-to-image workflow"`
- `"Apply the Wan 2.1 video generation template"`
- `"Give me a complete img2img workflow with upscale"`

It will search the template library or generate the workflow and apply it to the canvas. If required models are missing, the assistant will tell you what to download and where.

---

## Advanced Features

### 🚀 Workflow Execution
You can ask the assistant to run your workflow:
- `"Run the current workflow"`
- `"Generate an image with the prompt 'a futuristic city'"`

### 🔍 Research Tools
The assistant can search the web or the Comfy Registry:
- `"Search for a tutorial on ControlNet for ComfyUI"`
- `"Find the Impact Pack custom node on the registry"`
- `"What is the best model for hyperrealistic portraits? Search the web."`

### 💾 User Skills
Tell the assistant to remember your preferences:
- `"Remember to always use Preview Image instead of Save Image"`
- `"From now on, use SDXL Turbo for quick tests"`
- You can manage these with `/skills` or `/skill <name>`.

---

## Slash Commands
Type `/` in the chat to see available quick actions:
- `/help`: Show available commands and tools.
- `/clear`: Clear the current conversation history.
- `/new`: Start a new session.
- `/rename <name>`: Rename the current session.
- `/sessions`: List all saved chat sessions.

---

## Troubleshooting

### No response from Assistant
1. Check your `.env` file for correct API keys and URLs.
2. Check the ComfyUI terminal/console for backend errors.
3. Ensure you have an active internet connection for the LLM provider.

### Tools not appearing on canvas
1. Open the browser console (**F12**) to check for JavaScript errors.
2. Ensure you are using a modern version of ComfyUI with the new frontend.

---

**Happy Workflow Building!** ✨
