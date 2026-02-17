# Tavily Web Search Integration

## Current State

Web search is supported via SearXNG (`SEARXNG_URL` env var) and DuckDuckGo fallback (`ddgs`), but Tavily API integration is not available.

## Proposed Solution

- Add Tavily API as an additional web search provider option
- Implement Tavily search adapter in `web_search.py`
- Support Tavily-specific features (answer generation, content extraction, real-time search)
- Add Tavily API key configuration in Provider Wizard or environment variables
- Allow users to choose search provider (SearXNG, DuckDuckGo, or Tavily)

## Benefits

- High-quality search results optimized for AI/RAG use cases
- Built-in answer generation and content extraction
- Real-time search capabilities
- Better integration with research workflows

## Implementation Notes

- Add Tavily client to `web_search.py` (similar to SearXNG implementation)
- Add `TAVILY_API_KEY` environment variable
- Update `webSearch` tool to support provider selection
- Add Tavily configuration to Provider Wizard (optional, can be env-only)

## Related Files

- `web_search.py` - Web search provider abstraction
- `tools_definitions.py` - Tool declarations
- `ui/src/tools/implementations/web-search.ts` - Web search tool implementation
- `.env.example` - Environment variable template
- `doc/configuration.md` - Configuration documentation

## Tavily API Features

- **Answer Generation**: Get direct answers to queries
- **Content Extraction**: Extract clean content from web pages
- **Real-time Search**: Access to latest web content
- **RAG Optimization**: Results optimized for retrieval-augmented generation
- **Source Attribution**: Includes source URLs and metadata

## API Reference

- [Tavily API Documentation](https://docs.tavily.com/)
- [Tavily Python SDK](https://github.com/tavily/tavily-python)

## Configuration

Add to `.env`:
```bash
TAVILY_API_KEY=tvly-xxx
```

Or configure via Provider Wizard UI (when implemented).
