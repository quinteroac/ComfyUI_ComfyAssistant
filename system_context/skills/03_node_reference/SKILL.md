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
