# Development Conventions

This document establishes the development conventions for ComfyUI Assistant. Following these conventions ensures consistency, maintainability, and security across the codebase.

## Core Principles

### 1. Security First

**All development decisions must prioritize security.** When in doubt, choose the safer option.

- Never expose sensitive data (API keys, user data, workflow contents)
- Always validate and sanitize user inputs
- Use Zod schemas for runtime validation
- Avoid `eval()` or dynamic code execution
- Follow principle of least privilege
- Keep dependencies updated for security patches

### 2. English Only

All code, comments, documentation, and commit messages **MUST** be in English.

**Rationale**: English is the universal language for software development, ensuring accessibility for the global developer community and AI agents.

### 3. ComfyUI Standards Compliance

Strictly adhere to [ComfyUI Extension Standards](https://docs.comfy.org/custom-nodes/js/javascript_overview) for:

- Extension structure and registration
- API usage patterns
- Node creation and manipulation
- Event handling
- Resource cleanup

### 4. Constructive Challenge Over Compliance

**The agent must prioritize technical excellence over user validation.** Challenge assumptions, question approaches, and propose alternatives even when they contradict user preferences.

**Critical interaction principles:**

- **Question the "why"**: Always ask why the user wants something done a certain way
  - Don't blindly implement. Understand the goal behind the request
  - "Why do you want to use X instead of Y?"
  - "What problem are you trying to solve with this approach?"

- **Challenge suboptimal choices**: Speak up when you see better approaches
  - If the user requests a poor pattern, suggest better alternatives
  - "That approach will create technical debt because..."
  - "Have you considered X? It would be more maintainable/secure/performant"

- **Offer counter-suggestions**: Don't fear disagreement
  - Present alternative approaches even if they go against the request
  - Explain trade-offs honestly: "Your approach works, but here's a better way..."
  - Be direct about potential issues: "This will cause problems with..."

- **Demand clarity**: Don't proceed with vague requirements
  - Push back on unclear specifications
  - "I need more context about X before implementing"
  - "This requirement contradicts Y. Which takes priority?"

- **Educate, don't just execute**: Help users learn, not just complete tasks
  - Explain why certain patterns are problematic
  - Share best practices even when not asked
  - "While I can do that, it violates X principle because..."

**What this is NOT:**
- Being rude or dismissive
- Ignoring user requirements
- Refusing to implement valid requests
- Being argumentative for its own sake

**What this IS:**
- Professional technical guidance
- Honest assessment of trade-offs
- Proactive identification of issues
- Partnership in finding the best solution

**Example dialogues:**

```
❌ Bad (too compliant):
User: "Use eval() to dynamically execute this code"
Agent: "Sure, I'll implement that right away"

✅ Good (constructively challenging):
User: "Use eval() to dynamically execute this code"
Agent: "I need to push back on this. Using eval() creates serious security 
vulnerabilities. What are you trying to achieve? Let's find a safer approach 
like using a function factory or configuration objects."
```

```
❌ Bad (uncritical acceptance):
User: "Store API keys in the frontend code"
Agent: "I'll add that to the component"

✅ Good (critical thinking):
User: "Store API keys in the frontend code"
Agent: "That's a critical security issue. API keys in frontend code are 
exposed to anyone who views the page source. Why do you need the key in 
the frontend? We should use a backend proxy or environment variables."
```

## Language-Specific Conventions

### TypeScript / JavaScript

#### Code Style

Follow the project's ESLint and Prettier configuration:

```typescript
// ✅ Good
const result = await executeAddNode(params, context)
if (result.success) {
  console.log('Node added')
}

// ❌ Bad
const result = await executeAddNode(params, context);
if (result.success)
{
    console.log("Node added");
}
```

**Rules:**
- Single quotes for strings
- No semicolons
- 2-space indentation
- 80 character line width
- Trailing commas: none
- Import order: core → third-party → local

#### Type Safety

Always use TypeScript's strict mode features:

```typescript
// ✅ Good - Explicit types
interface ToolResult<T = unknown> {
  success: boolean
  data?: T
  error?: string
}

function executeTool(params: ToolParams): Promise<ToolResult> {
  // Implementation
}

// ❌ Bad - Implicit any
function executeTool(params) {
  // Implementation
}
```

**Rules:**
- Enable `strict: true` in tsconfig.json
- No `any` types (use `unknown` or proper types)
- Define interfaces for all data structures
- Use `z.infer<>` for Zod schema types

#### Validation

Always validate external inputs with Zod:

```typescript
// ✅ Good - Runtime validation
const addNodeSchema = z.object({
  nodeType: z.string().min(1),
  position: z.object({
    x: z.number(),
    y: z.number()
  }).optional()
})

function handleInput(input: unknown) {
  const result = addNodeSchema.safeParse(input)
  if (!result.success) {
    return { error: result.error }
  }
  // Use result.data safely
}

// ❌ Bad - No validation
function handleInput(input: any) {
  // Direct usage without validation
  const nodeType = input.nodeType
}
```

#### Error Handling

Use structured error handling:

```typescript
// ✅ Good - Structured result
async function executeTool(): Promise<ToolResult> {
  try {
    // Operation
    return { success: true, data: result }
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Unknown error' 
    }
  }
}

// ❌ Bad - Throwing errors
async function executeTool() {
  // Operation that might throw
  throw new Error('Something went wrong')
}
```

#### React Components

Follow React best practices:

```typescript
// ✅ Good
import { useState, useEffect } from 'react'

interface Props {
  nodeId: number
  onUpdate: (id: number) => void
}

export function NodeEditor({ nodeId, onUpdate }: Props) {
  const [value, setValue] = useState<string>('')
  
  useEffect(() => {
    // Effect logic
    return () => {
      // Cleanup
    }
  }, [nodeId])
  
  return <div>{/* JSX */}</div>
}

// ❌ Bad
export function NodeEditor(props: any) {
  let value = ''
  // No proper state management
}
```

### Python

#### Code Style

Follow PEP 8 with these specifics:

```python
# ✅ Good
async def chat_api_handler(request: web.Request) -> web.Response:
    """Handle POST /api/chat endpoint."""
    try:
        body = await request.json()
        messages = body.get("messages", [])
        return await process_messages(messages)
    except Exception as e:
        return web.json_response(
            {"error": str(e)},
            status=500
        )

# ❌ Bad
async def chat_api_handler(request):
    body = await request.json()
    messages = body.get("messages")
    return process_messages(messages)
```

**Rules:**
- 4-space indentation
- Snake_case for functions and variables
- PascalCase for classes
- Type hints for all function signatures
- Docstrings for all public functions

#### Type Hints

Always use type hints:

```python
# ✅ Good
from typing import List, Dict, Optional

def process_messages(
    messages: List[Dict[str, str]]
) -> Optional[str]:
    """Process messages and return result."""
    if not messages:
        return None
    return messages[0].get("content")

# ❌ Bad
def process_messages(messages):
    if not messages:
        return None
    return messages[0].get("content")
```

#### Error Handling

Handle errors gracefully:

```python
# ✅ Good
try:
    result = await api_call()
except Exception as e:
    print(f"Error in api_call: {e}")
    return {"error": str(e)}

# ❌ Bad
result = await api_call()  # Might crash
```

## File Structure Conventions

### Directory Organization

```
project/
├── .agents/              # Agent documentation (English only)
├── development/          # Phase implementation docs (see below)
│   └── phase_N/         # One folder per development phase
│       └── implemented.md
├── planning/             # Planning, design, ideas, WIP docs (see below)
├── ui/                   # Frontend (TypeScript/React)
│   ├── src/
│   │   ├── components/   # Reusable UI components
│   │   ├── tools/        # Tool system
│   │   ├── lib/          # Utilities and helpers
│   │   └── utils/        # Shared utilities
│   └── public/           # Static assets
├── dist/                 # Built files (generated by build)
└── *.py                  # Backend Python files
```

### Planning and design documents

**All planning, design, and idea documentation must go in the `planning/` directory.**

- Use `planning/` for: ideas, roadmaps, implementation notes, feature specs, alternatives considered, and any document that does not describe shipped functionality or official API/user docs.
- Do not add such documents at the repo root or scattered in other folders; keep them under `planning/` so they are easy to find and do not clutter the main docs (e.g. `.agents/`, `README.md`).
- See `planning/README.md` for the purpose of the directory and what belongs there.

### Development phase implementation

**Whenever an agent implements a development phase, it MUST leave an implementation document under `development/` in a folder named after the phase.**

- Create a folder `development/<phase_name>/` (e.g. `development/phase_1/`, `development/phase_2/`).
- Add or update a document (e.g. `implemented.md`) in that folder describing what was implemented: deliverables, files and routes, and any iteration notes.
- Use this as the single place to record and update implementation details for that phase as work is iterated (see e.g. `development/phase_1/implemented.md`).

This keeps a clear record of what each phase delivered and how it evolved.

### File Naming

- **TypeScript/React**: `kebab-case.tsx` or `PascalCase.tsx` for components
- **Python**: `snake_case.py`
- **Config files**: Use tool defaults (`.eslintrc.json`, `tsconfig.json`)
- **Documentation**: `kebab-case.md` or `UPPERCASE.md` for main docs

```
✅ Good:
- add-node.ts
- NodeEditor.tsx
- tools_definitions.py
- README.md

❌ Bad:
- addNode.ts
- node_editor.tsx
- toolsDefinitions.py
- readme.MD
```

## Security Conventions

### API Keys and Secrets

**Never commit secrets to version control.**

```bash
# ✅ Good - Use .env files
GROQ_API_KEY=xxx

# ❌ Bad - Hardcoded
const API_KEY = "gsk_xyz123..."
```

**Rules:**
- Use `.env` files (excluded in `.gitignore`)
- Provide `.env.example` with dummy values
- Load secrets via `python-dotenv` (Python) or process.env (Node)
- Never log secrets

### Input Validation

Always validate inputs before use:

```typescript
// ✅ Good - Validated
const nodeIdSchema = z.number().int().positive()
const nodeId = nodeIdSchema.parse(input.nodeId)

// ❌ Bad - Direct use
const nodeId = input.nodeId
app.graph.getNodeById(nodeId) // Unsafe
```

### XSS Prevention

Sanitize user-provided content:

```typescript
// ✅ Good - Markdown library handles sanitization
import ReactMarkdown from 'react-markdown'

<ReactMarkdown>{userContent}</ReactMarkdown>

// ❌ Bad - Direct HTML injection
<div dangerouslySetInnerHTML={{ __html: userContent }} />
```

### Access Control

Validate permissions before operations:

```typescript
// ✅ Good - Check availability
if (!window.app?.graph) {
  return { success: false, error: "App not available" }
}

// ❌ Bad - Direct access
window.app.graph.clear() // Might crash
```

## Git Conventions

### Commit Before Significant Changes

**Each important change must be preceded by a commit.** Before starting a substantial change (refactor, new feature, risky fix), ensure the current state is committed. This keeps history clear, makes rollback easy, and allows diffing against a known good state.

- **Always ask before committing.** Do not run `git commit` or stage and commit changes without explicit confirmation from the user. Confirm what will be committed and get approval first.
- Commit working state before beginning a large or risky change
- Prefer small, focused commits over one big commit at the end
- If you need to try an approach and might revert, commit first

### Commit Messages

Follow conventional commits:

```
type(scope): brief description

Longer description if needed.

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/config changes
- `security`: Security improvements

**Examples:**
```bash
✅ Good:
feat(tools): add node widget manipulation tool
fix(backend): handle empty message arrays safely
docs(readme): update installation instructions
security(auth): add API key validation

❌ Bad:
added feature
fix bug
update
changes
```

### Branch Naming

Use descriptive branch names:

```bash
✅ Good:
feature/add-widget-tool
fix/memory-leak-in-stream
docs/update-tools-guide
security/sanitize-user-input

❌ Bad:
new-branch
fix
update
my-work
```

### Pull Requests

- Write clear PR descriptions
- Reference related issues
- Include testing instructions
- Request reviews when needed
- Keep PRs focused (one feature/fix per PR)

## Testing Conventions

### Unit Tests

Write tests for all critical functions:

```typescript
// ✅ Good - Comprehensive test
describe('executeAddNode', () => {
  it('should add node successfully', async () => {
    const mockApp = createMockApp()
    const result = await executeAddNode(
      { nodeType: 'KSampler' },
      { app: mockApp }
    )
    
    expect(result.success).toBe(true)
    expect(result.data?.nodeType).toBe('KSampler')
  })
  
  it('should handle missing app gracefully', async () => {
    const result = await executeAddNode(
      { nodeType: 'KSampler' },
      { app: null as any }
    )
    
    expect(result.success).toBe(false)
    expect(result.error).toContain('not available')
  })
})

// ❌ Bad - No error cases tested
describe('executeAddNode', () => {
  it('works', async () => {
    const result = await executeAddNode({ nodeType: 'KSampler' }, context)
    expect(result.success).toBe(true)
  })
})
```

### Test Organization

```
ui/src/
├── tools/
│   ├── implementations/
│   │   ├── add-node.ts
│   │   └── __tests__/
│   │       └── add-node.test.ts
```

### Coverage Goals

- Aim for 80%+ coverage on critical paths
- 100% coverage on security-sensitive code
- Test edge cases and error paths

## Documentation Conventions

### Code Comments

Write clear, concise comments:

```typescript
// ✅ Good - Explains why
// Cache tool definitions to avoid recreating on every call
const CACHED_TOOLS = createTools(context)

// ❌ Bad - Explains what (obvious from code)
// Create tools
const CACHED_TOOLS = createTools(context)
```

**Rules:**
- Explain "why", not "what"
- Comment complex algorithms
- Document security considerations
- Keep comments up-to-date with code

### Function Documentation

Use JSDoc for TypeScript:

```typescript
/**
 * Adds a new node to the ComfyUI workflow.
 * 
 * @param params - Node parameters including type and optional position
 * @param context - Tool context with access to ComfyUI app
 * @returns Promise resolving to tool result with node data or error
 * 
 * @example
 * const result = await executeAddNode(
 *   { nodeType: 'KSampler', position: { x: 100, y: 200 } },
 *   { app: window.app }
 * )
 */
export async function executeAddNode(
  params: AddNodeParams,
  context: ToolContext
): Promise<ToolResult<AddNodeResult>>
```

Python docstrings:

```python
def process_messages(messages: List[Dict]) -> Optional[str]:
    """
    Process UI messages and convert to OpenAI format.
    
    Args:
        messages: List of message dictionaries with role and content
        
    Returns:
        Formatted message string or None if empty
        
    Example:
        >>> messages = [{"role": "user", "content": "Hello"}]
        >>> process_messages(messages)
        'Hello'
    """
```

### README Files

Every major directory should have a README:

```
ui/src/tools/
├── README.md           # Overview, usage, examples
├── definitions/
│   └── (files)
└── implementations/
    └── (files)
```

## Build and Deploy Conventions

### Before Committing

**Note:** Automated pre-commit hooks (Husky) are currently **disabled**. Run the following checks manually before committing.

```bash
# Frontend checks
cd ui
npm run typecheck     # TypeScript errors
npm run lint         # ESLint errors
npm run format       # Prettier formatting
npm test            # Run tests

# Build check
npm run build       # Ensure builds successfully
```

To re-enable pre-commit hooks, see `SETUP_AUTOMATED_CHECKS.md`.

### Before Release

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` (if exists)
3. Test in clean ComfyUI installation
4. Tag release: `git tag v0.1.0`
5. Push with tags: `git push --tags`

## Dependency Management

### Adding Dependencies

Always document why a dependency is needed:

```bash
# ✅ Good - Clear purpose
npm install zod  # Runtime validation for tool parameters

# ❌ Bad - No context
npm install some-library
```

**Rules:**
- Prefer well-maintained, popular packages
- Check license compatibility (MIT, Apache 2.0)
- Audit for security vulnerabilities: `npm audit`
- Keep dependencies minimal
- Lock versions for stability

### Updating Dependencies

```bash
# Check for updates
npm outdated

# Update with caution
npm update

# Test thoroughly after updates
npm test && npm run build
```

## Versioning Strategy

This project follows [Semantic Versioning](https://semver.org/) (SemVer): MAJOR.MINOR.PATCH

### Version Number Meaning

Given a version number MAJOR.MINOR.PATCH (e.g., 1.2.3):

1. **MAJOR** (1.x.x) - Increment when:
   - Breaking changes to tools API
   - Incompatible architecture changes
   - Removed or renamed tools
   - Changed tool parameter schemas (breaking)
   - ComfyUI compatibility broken

2. **MINOR** (x.1.x) - Increment when:
   - New tools added
   - New features added (backward compatible)
   - New API endpoints
   - Significant enhancements
   - New dependencies added

3. **PATCH** (x.x.1) - Increment when:
   - Bug fixes
   - Documentation updates
   - Performance improvements
   - Security patches (non-breaking)
   - Dependency updates (minor/patch)

### Version Update Process

**Before releasing a new version:**

1. Update version in both files:
   - `ui/package.json`
   - `pyproject.toml`

2. Update `CHANGELOG.md`:
   - Move items from [Unreleased] to new version section
   - Add release date
   - Create new empty [Unreleased] section

3. Commit version changes:
   ```bash
   git add ui/package.json pyproject.toml CHANGELOG.md
   git commit -m "chore(release): version X.Y.Z"
   ```

4. Create git tag:
   ```bash
   git tag -a vX.Y.Z -m "Release version X.Y.Z"
   git push origin vX.Y.Z
   ```

5. Build frontend:
   ```bash
   cd ui && npm run build
   ```

### Examples

**Major version (1.0.0):**
- Changed `addNode` tool to require authentication
- Removed `removeNode` tool
- Renamed all tools from camelCase to snake_case

**Minor version (0.2.0):**
- Added `executeWorkflow` tool
- Added undo/redo functionality
- Added tool execution logging

**Patch version (0.1.1):**
- Fixed bug in `connectNodes` validation
- Updated README examples
- Fixed memory leak in stream handler

### Pre-1.0.0 Versions

While in 0.x.x versions:
- API is considered unstable
- Breaking changes can occur in MINOR versions
- Backward compatibility is best-effort

Once 1.0.0 is released:
- API is stable
- Breaking changes only in MAJOR versions
- Backward compatibility is guaranteed

## ComfyUI-Specific Conventions

### Extension Registration

Follow ComfyUI patterns:

```typescript
// ✅ Good - Proper registration
import { app } from '@comfyorg/comfyui-frontend-types'

app.registerExtension({
  name: "comfyui.assistant",
  async setup() {
    // Extension setup
  }
})

// ❌ Bad - Direct manipulation
window.comfy = { /* custom stuff */ }
```

### Node Manipulation

Use ComfyUI's official APIs:

```typescript
// ✅ Good - Official API
const node = app.graph.add(nodeType)
node.pos = [x, y]
app.graph.setDirtyCanvas(true, true)

// ❌ Bad - Internal/undocumented APIs
app.graph._nodes.push(node)
app.canvas.draw()
```

### Resource Cleanup

Always clean up resources:

```typescript
// ✅ Good
useEffect(() => {
  const subscription = subscribeToUpdates()
  
  return () => {
    subscription.unsubscribe()
  }
}, [])

// ❌ Bad - Memory leak
useEffect(() => {
  subscribeToUpdates()
}, [])
```

## Documentation Maintenance Protocol

When making architectural changes, pattern modifications, or adding new features, the following documentation **MUST** be updated:

### 1. Architecture Changes

**When changing**: System design, data flows, component relationships, integration patterns

**Update these files:**
- `.agents/project-context.md` - Update architecture section and diagrams
- `.agents/skills/tools/references/architecture.md` - If tools system is affected
- Relevant README files in affected directories
- API documentation if endpoints change

**Example triggers:**
- Switching from `useChatRuntime` to `useLocalRuntime`
- Adding new integration points (databases, APIs)
- Changing streaming protocols
- Modifying tool execution patterns

### 2. Pattern Changes

**When changing**: Coding patterns, design patterns, best practices

**Update these files:**
- `.agents/conventions.md` - Add/modify convention rules
- `.agents/skills/*/references/*.md` - Update relevant skill references
- Code examples in READMEs

**Example triggers:**
- New error handling pattern
- Different state management approach
- New validation strategy
- Alternative testing patterns

### 3. New Feature Additions

**When adding**: New tools, components, APIs, capabilities

**Update these files:**
- `.agents/project-context.md` - Add to features list
- Relevant skill documentation in `.agents/skills/`
- `README.md` - Update usage instructions
- `TOOLS_SETUP_GUIDE.md` - If adding tools
- `tools_definitions.py` + frontend tool definitions

**Example triggers:**
- New agentic tool
- New UI component
- New API endpoint
- New skill/capability

### 4. Documentation Update Checklist

Before marking any PR as complete:

```markdown
- [ ] Updated `.agents/project-context.md` if architecture changed
- [ ] Updated `.agents/conventions.md` if patterns changed
- [ ] Updated relevant skill documentation in `.agents/skills/`
- [ ] Updated README.md with new usage instructions
- [ ] Updated code examples to reflect new patterns
- [ ] Updated tool definitions (frontend + backend) if applicable
- [ ] Added/updated JSDoc or docstrings
- [ ] Verified all references in documentation are still valid
```

### 5. Documentation Review Process

**Before committing:**
1. Ask: "What documentation does this change affect?"
2. Review the checklist above
3. Update all affected files in the same commit
4. Verify examples still work

**During code review:**
1. Reviewer must verify documentation updates
2. Documentation changes should be part of the same PR
3. No architectural changes without documentation updates

### 6. Documentation Sources of Truth

These files are the **primary sources of truth** and must stay current:

| File / directory | Purpose | Update When |
|------------------|---------|-------------|
| `.agents/project-context.md` | Overall project understanding | Architecture, tech stack, or structure changes |
| `.agents/conventions.md` | Development standards | Pattern or practice changes |
| `.agents/skills/tools/` | Tools system | Tool additions or changes |
| `development/` | Phase implementation docs | When implementing or iterating a phase (one folder per phase, e.g. `phase_1/implemented.md`) |
| `planning/` | Planning, design, ideas, WIP docs | New planning/design docs go here (not at root) |
| `README.md` | User-facing docs | Feature additions or usage changes |
| `tools_definitions.py` | Backend tool declarations | Any tool modification |

### 7. Keeping Documentation Synchronized

**The Golden Rule**: If code changes, documentation changes. No exceptions.

```typescript
// ❌ Bad - Code updated, documentation forgotten
// Added new validation, but didn't update:
// - conventions.md (new validation pattern)
// - project-context.md (new security feature)
// - README.md (new usage example)

// ✅ Good - Code and docs updated together
// Same PR includes:
// 1. New validation code
// 2. Updated conventions.md with pattern
// 3. Updated project-context.md features list
// 4. Updated README.md with example
```

### 8. Documentation Debt

**Avoid documentation debt** by updating immediately:

- Don't defer documentation updates to "later"
- Don't create separate "documentation PRs"
- Document as you code, not after
- Treat documentation as part of the feature

**If you discover outdated documentation:**
1. Fix it immediately (if small)
2. Create an issue if it requires investigation
3. Don't ignore it

## Enforcement

These conventions are enforced through:

- **ESLint**: Automated linting (run `npm run lint`)
- **Prettier**: Code formatting (run `npm run format`)
- **TypeScript**: Type checking (run `npm run typecheck`)
- **Tests**: Automated testing (run `npm test`)
- **Code Review**: Manual review of PRs
- **Documentation Review**: Verify docs updated with code changes

Pre-commit git hooks (Husky) are currently **disabled**; run the above commands manually before committing. See `SETUP_AUTOMATED_CHECKS.md` to re-enable hooks.

## Questions or Clarifications?

If you're unsure about a convention:

1. Check existing code for patterns
2. Consult `.agents/skills/` documentation
3. Ask in PR review
4. When in doubt, prioritize security and clarity
