---
name: template-library
description: Unified workflow template library (official and community). Use this as the primary starting point for any complex model request (Wan, Flux, SDXL, etc.).
---

# Template Library (Official & Community)

You have access to an extensive library of high-quality, pre-defined workflows (templates).

## How to use (Model Agnostic Flow)

1. **Search**: Call `searchTemplates(query)` with the model name or task.
2. **Apply**: Call `applyTemplate(id, source, package)` directly. **Do not wait to check if the user has the models first.**
3. **Analyze & Inform**: 
   - After applying, the tool will return `referencedModels`.
   - Call `getAvailableModels()` to see what the user actually has.
   - Compare the two lists.
   - **If models are missing**: Inform the user clearly. "I've loaded the workflow, but you are missing the following models: [List]. You should download them to your [checkpoints/unet/vae] folder."
4. **Finalize**: Adjust prompts or basic settings if requested.

## Guidelines

- **Implement first, ask later**: Always provide the workflow structure even if the user lacks the models. This allows the user to see the required setup and know exactly what to download.
- **Node Validation**: If the tool returns warnings about "unknown types", inform the user which custom node packages they need to install from the Registry.
- **Randomize**: When setting up templates, use random seeds so the user can run it immediately after getting the models.

## Example Flow

User: "I want to try Wan 2.1 video generation"
1. `searchTemplates(query: "wan")`
2. Found `video_wan2.1_t2v_14b`.
3. `applyTemplate(id: "video_wan2.1_t2v_14b", source: "official")`
4. Result shows it needs `wan2.1_t2v_14b_bf16.safetensors`.
5. `getAvailableModels()`
6. User doesn't have it.
7. You: "I've loaded the official Wan 2.1 template. Note: You don't have the required model `wan2.1_t2v_14b_bf16.safetensors` yet. Once you download it to your `diffusion_models` folder, you'll be able to run this workflow."
