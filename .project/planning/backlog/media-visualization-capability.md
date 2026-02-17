# Media Visualization Capability for LLM

## Current State

The agent can manipulate workflows and execute them, but cannot see the actual input/output media (images, videos) that workflows produce or consume.

## Proposed Solution

- Implement vision capabilities for supported LLM providers (GPT-4 Vision, Claude 3.5 Sonnet, Gemini Vision)
- Add image data extraction from ComfyUI outputs (base64 encoding or file paths)
- Include image data in tool results when media is involved
- Support both input images (for image-to-image workflows) and output images (for generation results)
- Add `getWorkflowOutputs` tool that returns image data along with metadata
- Update system prompts to guide the agent on using vision for workflow debugging and refinement

## Benefits

- Agent can verify workflow outputs visually
- Better debugging (agent can see what went wrong in generated images)
- Improved workflow refinement (agent can suggest improvements based on visual results)
- Support for image-based workflows (inpainting, upscaling, style transfer)

## Implementation Notes

- Add vision support to provider adapters (`provider_streaming.py`)
- Create `getWorkflowOutputs` tool that extracts image data from execution results
- Update tool result types to include optional image data fields
- Modify system prompts to include vision usage guidelines
- Consider image size limits and compression for API efficiency

## Related Files

- `provider_streaming.py` - Provider adapters (vision support)
- `ui/src/tools/implementations/execute-workflow.ts` - Workflow execution (output extraction)
- `ui/src/tools/definitions/` - Tool schema definitions
- `system_context/skills/` - System prompt skills
- `agent_prompts.py` - System message assembly

## Technical Considerations

- **Image Format**: Base64 encoding vs file paths (base64 preferred for API compatibility)
- **Size Limits**: Provider-specific image size limits (e.g., GPT-4 Vision: 20MB, Claude: 5MB)
- **Compression**: May need to compress large images before sending to API
- **Multiple Images**: Support for workflows with multiple outputs
- **Video Support**: Future consideration for video workflows

## Supported Providers

- **OpenAI GPT-4 Vision**: Full support
- **Anthropic Claude 3.5 Sonnet**: Full support
- **Google Gemini Vision**: When Gemini API support is added
- **Other providers**: Check provider-specific vision capabilities
