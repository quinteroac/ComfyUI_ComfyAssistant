# Enhanced User Preferences and Memory System

## Current State

Basic preferences exist in `user_context/context.db` (`preferences` table), but the system lacks a robust way for users to express workflow preferences that persist across conversations.

## Proposed Solution

- Extend preferences system to support natural language preference declarations
- Create a `setPreference` tool that allows users to state preferences like "I prefer preview nodes over save nodes" or "always use CFG scale 7"
- Store preferences with semantic keys (e.g., `workflow.output_method: preview`, `sampling.cfg_scale: 7`)
- Inject relevant preferences into system context when building workflows
- Add preference management UI (view/edit/delete preferences)
- Support preference inheritance and overrides

## Benefits

- Personalized workflow generation (agent remembers user preferences)
- Reduced repetition (user doesn't need to specify preferences every time)
- Better user experience (workflows match user's style automatically)

## Implementation Notes

- Extend `user_context_store.py` with preference parsing and semantic storage
- Create `setPreference` tool (frontend + backend declaration)
- Update `agent_prompts.py` to inject preferences into system message
- Add preference management to Provider Wizard or separate settings panel

## Related Files

- `user_context_store.py` - User context and preferences storage
- `agent_prompts.py` - System message assembly
- `tools_definitions.py` - Tool declarations
- `ui/src/tools/` - Tool implementations
- `user_context/context.db` - Preferences database

## Example Preferences

- `workflow.output_method: preview` - Prefer preview nodes over save nodes
- `sampling.cfg_scale: 7` - Default CFG scale
- `sampling.steps: 20` - Default sampling steps
- `workflow.resolution: 1024x1024` - Preferred image resolution
- `models.checkpoint: sd_xl_base_1.0.safetensors` - Preferred checkpoint model
