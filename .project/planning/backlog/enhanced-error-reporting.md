# Enhanced Error Reporting from ComfyUI API

## Current State

The agent detects workflow execution failures but lacks visibility into the specific error details returned by ComfyUI's API. When `executeWorkflow` returns an error status, the agent knows that execution failed but cannot see the root cause (e.g., missing model files, invalid node connections, memory errors, etc.).

## Proposed Solution

- Capture and parse detailed error messages from ComfyUI's execution API responses
- Include node-specific error information (node IDs, error types, validation messages)
- Pass structured error details to the agent in tool results
- Update system prompts to guide the agent on interpreting and fixing common error types
- Enable the agent to automatically retry with corrections (e.g., switching to available models, fixing connections)

## Benefits

- Faster debugging cycles (agent can self-correct simple issues)
- Better user experience (more actionable error messages)
- Reduced back-and-forth between user and agent

## Implementation Notes

- Modify `execute-workflow.ts` to extract error details from ComfyUI API responses
- Enhance error result structure in `ExecuteWorkflowResult` type
- Update `05_workflow_execution/SKILL.md` with error interpretation guidelines

## Related Files

- `ui/src/tools/implementations/execute-workflow.ts` - Main workflow execution tool
- `ui/src/tools/definitions/execute-workflow.ts` - Tool schema definition
- `system_context/skills/05_workflow_execution/SKILL.md` - Workflow execution guidelines
- `provider_streaming.py` - Error handling in streaming responses
