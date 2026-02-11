---
name: model-loading-rules
description: Rules for choosing Load Diffusion Model vs CheckpointLoader based on where the model is installed (diffusion_models/unet vs checkpoints).
---

# Model loading rules (ComfyUI)

Use these rules when deciding how to load a model:

## 1) UNet-style models

- If the model exists under **`diffusion_models`** or **`unet`**, load it with **Load Diffusion Model** (class type `UNETLoader`).
- In this case, **you must also load VAE and CLIP separately** (e.g., `VAELoader` and `CLIPLoader` or `DualCLIPLoader` as required by the workflow).

## 2) Checkpoint models

- If the model exists under **`checkpoints`**, load it with **CheckpointLoaderSimple**.
- Checkpoints already include **MODEL + VAE + CLIP**, so do **not** load separate VAE/CLIP unless the user explicitly asks to override them.

## Required validation

- Always use `getAvailableModels` to determine the model category before choosing the loader.
- If a ComfyUI_examples workflow exists for the model family, **follow its loader choice** even if you would normally choose a different loader.
- Never guess the model’s location or loader type.
