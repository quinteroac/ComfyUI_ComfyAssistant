---
name: node-reference
description: Common ComfyUI node types and workflow patterns. Use when suggesting nodes or explaining workflows.
---

# Common Node Types Reference

This reference helps you suggest appropriate nodes for user needs.

## Loaders & Models

- **CheckpointLoaderSimple**: Loads SD model (outputs: MODEL, CLIP, VAE)
- **LoraLoader**: Adds LoRA to model (inputs: MODEL, CLIP)
- **VAELoader**: Loads separate VAE
- **ControlNetLoader**: Loads ControlNet models

## Conditioning (Prompts)

- **CLIPTextEncode**: Positive/negative prompts (input: CLIP, text)
- **ConditioningCombine**: Combines multiple conditionings
- **ConditioningSetArea**: Area conditioning for inpainting

## Latents

- **EmptyLatentImage**: Creates blank latent (specify width/height)
- **VAEEncode**: Image to latent (input: VAE, IMAGE)
- **VAEDecode**: Latent to image (input: VAE, LATENT)
- **LatentUpscale**: Upscale latents

## Sampling

- **KSampler**: Standard sampler (inputs: MODEL, LATENT, positive, negative)
- **KSamplerAdvanced**: More control over sampling
- **SamplerCustom**: Custom sampling pipeline

## Image Processing

- **LoadImage**: Load from disk
- **SaveImage**: Save to disk
- **ImageScale**: Resize images
- **ImageUpscaleWithModel**: AI upscaling
- **ImageBatch**: Combine images into batch

## Utilities

- **PrimitiveNode**: Store constants/values
- **Reroute**: Clean up connections
- **Note**: Add notes/comments

## Common Workflows

**Basic txt2img:**
CheckpointLoaderSimple → KSampler → VAEDecode → SaveImage
                      ↓
              CLIPTextEncode (positive)
              CLIPTextEncode (negative)
              EmptyLatentImage

**img2img:**
CheckpointLoaderSimple → KSampler → VAEDecode → SaveImage
LoadImage → VAEEncode ↗

## Common Widget Names

Use these with `setNodeWidgetValue`. Call `getWorkflowInfo` with `includeNodeDetails: true` to confirm exact names.

- **KSampler**: seed, steps (number), cfg (number), sampler_name (string: "euler", "euler_ancestral", "dpmpp_2m", etc.), scheduler (string: "normal", "karras", "exponential", etc.), denoise (number: 0.0–1.0)
- **EmptyLatentImage**: width (number), height (number), batch_size (number)
- **CLIPTextEncode**: text (string) — use `fillPromptNode` for convenience
- **SaveImage**: filename_prefix (string)
- **KSamplerAdvanced**: add_noise ("enable"/"disable"), noise_seed, steps, cfg, sampler_name, scheduler, start_at_step, end_at_step, return_with_leftover_noise ("disable"/"enable")
- **ImageScale**: upscale_method (string), width (number), height (number), crop (string)

## Prompt Writing Guide

When filling CLIPTextEncode text widgets:

**Positive prompt structure**: subject, style/medium, quality modifiers, lighting/mood
- Example: "a fluffy orange cat sitting on a windowsill, digital painting, highly detailed, warm afternoon sunlight"

**Negative prompt terms**: things to avoid in the generation
- Example: "blurry, low quality, deformed, ugly, watermark, text, oversaturated"

**Tips**:
- Be specific and descriptive for positive prompts
- Separate concepts with commas
- Quality terms like "masterpiece, best quality, highly detailed" can help
- For negative, list common artifacts to avoid
