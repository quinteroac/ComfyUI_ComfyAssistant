# Google Gemini API Support

## Current State

The extension supports OpenAI-compatible providers, Anthropic API, Claude Code CLI, Codex CLI, but Google Gemini API integration is not yet implemented.

## Proposed Solution

- Add Gemini API provider support following the existing provider pattern
- Implement streaming adapter for Gemini API (similar to `stream_openai` and `stream_anthropic`)
- Add Gemini provider configuration in Provider Wizard UI
- Support both Gemini API (REST) and Gemini CLI (if available)
- Store Gemini API key and model preferences in `providers.db`

## Benefits

- Access to Google's Gemini models (Gemini Pro, Gemini Ultra, etc.)
- More provider options for users
- Consistent provider management experience

## Implementation Notes

- Create `stream_gemini` function in `provider_streaming.py`
- Add Gemini provider type to `provider_manager.py`
- Update Provider Wizard UI to include Gemini configuration
- Add environment variables: `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_BASE_URL`

## Related Files

- `provider_streaming.py` - Provider streaming adapters
- `provider_manager.py` - Provider configuration management
- `provider_store.py` - Provider database storage
- `ui/src/components/` - Provider Wizard UI components
- `.env.example` - Environment variable template

## API Reference

- [Google Gemini API Documentation](https://ai.google.dev/docs)
- [Gemini API Models](https://ai.google.dev/models/gemini)
