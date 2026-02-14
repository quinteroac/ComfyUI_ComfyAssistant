# Provider Configuration Wizard - Implementation Plan

## Context

Currently, ComfyUI Assistant requires manual `.env` file configuration to set up LLM providers (OpenAI, Anthropic, Claude Code, Codex, Gemini CLI). This creates friction for users and makes it difficult to switch between providers or maintain multiple configurations.

This plan implements a **Provider Configuration Wizard** that:
- Provides a guided UI for configuring LLM providers
- Stores configurations in SQLite (not `.env`)
- Allows multiple API provider configurations (e.g., multiple OpenAI configs with different API keys)
- Enables runtime provider switching via slash commands
- Shows automatically on first use (similar to SOUL.md onboarding)

**User Requirements:**
- Wizard triggered on first use AND via `/provider-settings` command
- Support 5 providers: `claude_code`, `codex`, `gemini_cli`, `openai`, `anthropic`
- API providers (openai, anthropic): Multiple configs allowed with custom names
- CLI providers (claude_code, codex, gemini_cli): One config per type, name = provider_type
- SQLite storage with base64-encoded API keys (local deployment security)
- Commands: `/provider set <name>`, `/provider list`, `/provider-settings`
- UI style matching SOUL.md wizard (centered card, Tailwind CSS, shadcn components)

## Database Schema

**File:** `user_context/providers.db` (new SQLite database)

### Table: `providers`

```sql
CREATE TABLE providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_type TEXT NOT NULL,           -- 'openai', 'anthropic', 'claude_code', 'codex', 'gemini_cli'
    name TEXT NOT NULL UNIQUE,             -- Unique identifier (slug)
    display_name TEXT NOT NULL,            -- Human-friendly name shown in UI

    -- API Configuration (for openai, anthropic)
    api_key TEXT,                          -- Base64 encoded
    base_url TEXT,                         -- API endpoint URL
    model TEXT,                            -- Model name/ID

    -- Anthropic specific
    max_tokens INTEGER,                    -- Max output tokens

    -- CLI Configuration (for claude_code, codex, gemini_cli)
    cli_command TEXT,                      -- Path to CLI binary
    cli_model TEXT,                        -- Optional model selection
    timeout_seconds INTEGER DEFAULT 180,   -- CLI timeout

    -- Metadata
    is_active INTEGER DEFAULT 0,           -- Boolean: only one can be active
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    -- Constraints
    CHECK (
        -- CLI providers: name must equal provider_type
        (provider_type IN ('claude_code', 'codex', 'gemini_cli') AND name = provider_type)
        OR
        -- API providers: name can be custom
        (provider_type IN ('openai', 'anthropic'))
    ),
    CHECK (is_active IN (0, 1))
);

CREATE UNIQUE INDEX idx_providers_name ON providers(name);
CREATE INDEX idx_providers_active ON providers(is_active);
CREATE INDEX idx_providers_type ON providers(provider_type);

-- Ensure only one active provider
CREATE TRIGGER enforce_single_active_provider
BEFORE UPDATE OF is_active ON providers
WHEN NEW.is_active = 1
BEGIN
    UPDATE providers SET is_active = 0 WHERE is_active = 1 AND id != NEW.id;
END;

CREATE TRIGGER enforce_single_active_provider_insert
BEFORE INSERT ON providers
WHEN NEW.is_active = 1
BEGIN
    UPDATE providers SET is_active = 0 WHERE is_active = 1;
END;
```

**Design Notes:**
- CLI providers limited to one config each (enforced by CHECK constraint)
- API providers can have multiple configs (e.g., "openai-groq", "openai-official")
- API keys stored as base64 for minimal obfuscation (suitable for local deployment)
- Only one provider can be `is_active = 1` at a time (enforced by triggers)

## Wizard UI Flow

### Approach: Adaptive Multi-Step Wizard

**Display Mode:**
- **Full-page view** when no providers configured (first-time setup, like SOUL.md)
- **Modal dialog** when invoked via `/provider-settings` during conversation
- **Style:** Centered card layout matching SOUL.md wizard exactly

### Step 1: Provider Selection

**Component:** `ProviderSelectionScreen.tsx`

**UI Layout:**
- Heading: "Configure Your AI Provider"
- Subheading: "Choose a provider to get started"
- Grid of 5 provider cards (2 columns on desktop)
- Each card shows:
  - Provider logo/icon
  - Provider name (e.g., "Claude Code", "OpenAI")
  - Short description
  - "Configure" button
  - For CLI providers: Status indicator (✓ CLI available / ⚠️ CLI not found)

**Interaction:**
- Click "Configure" → proceed to Step 2 with selected provider
- CLI availability check runs on mount using backend endpoint

### Step 2: Provider Configuration

**Component:** `ProviderConfigScreen.tsx`

**Dynamic Form Based on Provider Type:**

#### For API Providers (OpenAI, Anthropic):
```typescript
Fields:
- displayName: text (required) - e.g., "OpenAI GPT-4"
- name: text (auto-generated slug from displayName, editable)
- apiKey: password (required) - API key
- baseUrl: text (optional) - Default based on provider type
- model: text (optional) - Model name, default based on provider
- maxTokens: number (Anthropic only, optional) - Default 4096
```

**Defaults:**
- OpenAI: `baseUrl = "https://api.openai.com/v1"`, `model = "gpt-4o"`
- Anthropic: `baseUrl = "https://api.anthropic.com"`, `model = "claude-sonnet-4-5"`, `maxTokens = 4096`

#### For CLI Providers (claude_code, codex, gemini_cli):
```typescript
Fields:
- name: text (read-only, equals provider_type)
- displayName: text (required) - e.g., "Claude Code"
- cliCommand: text (required) - Path to CLI binary, pre-filled if detected
- cliModel: text (optional) - Model selection (if supported by CLI)
- timeoutSeconds: number (optional) - Default 180
```

**CLI Detection:**
- Backend checks `shutil.which(default_command)` on mount
- If found: pre-fill `cliCommand` with detected path
- If not found: show warning + manual path entry

**Validation:**
- All required fields must be filled
- API keys: minimum length 20 characters
- URLs: valid HTTP/HTTPS format
- CLI paths: file exists and is executable (backend validation)

**UI Elements:**
- Form matching SOUL.md styling (space-y-6, rounded inputs)
- Help text under each field
- "Back" button (returns to Step 1)
- "Next" button (validates and proceeds to Step 3)

### Step 3: Confirmation & Test

**Component:** `ProviderConfirmScreen.tsx`

**UI Layout:**
- Summary card showing configured values
- "Test Connection" button
- Loading spinner during test
- Success/error message display
- "Set as Active Provider" checkbox (checked by default)
- Action buttons:
  - "Back" (return to edit)
  - "Save & Finish" (save and close wizard)
  - "Save & Add Another" (save and return to Step 1)

**Connection Test:**
- Sends minimal test request to provider
- Timeout: 10 seconds
- Shows detailed error messages on failure
- Test is optional (can skip and save)

**On Save:**
- Store provider in database (API key base64-encoded)
- If "Set as Active" checked: mark as active provider
- If "Save & Finish": close wizard and reload chat
- If "Save & Add Another": return to Step 1

## Backend Implementation

### New Module: `provider_store.py`

Pattern: Similar to `user_context_store.py`

**Core Functions:**

```python
def init_providers_db() -> None:
    """Initialize providers.db with schema."""

def get_all_providers() -> list[dict]:
    """Return all providers (API keys masked in response)."""

def get_provider_by_name(name: str) -> dict | None:
    """Get single provider by name."""

def get_active_provider() -> dict | None:
    """Get the currently active provider."""

def create_provider(data: dict) -> dict:
    """Create new provider, returns created record."""

def update_provider(name: str, data: dict) -> dict:
    """Update provider, returns updated record."""

def delete_provider(name: str) -> bool:
    """Delete provider, returns success."""

def set_active_provider(name: str) -> bool:
    """Set provider as active, deactivates others."""

def encode_api_key(key: str) -> str:
    """Base64 encode API key."""

def decode_api_key(encoded: str) -> str:
    """Base64 decode API key."""

def validate_provider_config(provider_type: str, data: dict) -> tuple[bool, str]:
    """Validate provider configuration, returns (valid, error_message)."""
```

**Validation Rules:**
- OpenAI: requires `api_key`, optional `base_url`, `model`
- Anthropic: requires `api_key`, optional `base_url`, `model`, `max_tokens`
- CLI: requires `cli_command` (must be executable), optional `cli_model`, `timeout_seconds`
- Name constraints: CLI names must equal provider_type, API names must be unique

### New Module: `provider_manager.py`

**Purpose:** Runtime provider management and initialization

```python
def get_current_provider_config() -> dict:
    """Get active provider config from database."""

def initialize_provider_from_db() -> str:
    """Initialize provider from database, returns provider_type."""

def reload_provider() -> bool:
    """Reload provider config (for runtime switching)."""

def test_provider_connection(name: str) -> tuple[bool, str]:
    """Test provider connection, returns (success, message)."""
```

**Integration with Existing Code:**

Current provider initialization (`__init__.py` lines 173-181) will be refactored:

```python
# OLD: Read from env vars
def _selected_llm_provider():
    if LLM_PROVIDER and LLM_PROVIDER in ("openai", "anthropic", ...):
        return LLM_PROVIDER
    # ... fallback logic

# NEW: Read from database first, fallback to env
def _selected_llm_provider():
    # Try database first
    active_provider = provider_store.get_active_provider()
    if active_provider:
        return active_provider['provider_type']

    # Fallback to env vars (for backward compatibility)
    if LLM_PROVIDER and LLM_PROVIDER in VALID_PROVIDERS:
        return LLM_PROVIDER
    # ... existing fallback logic
```

**Provider config loading** will also be updated to read from database:

```python
def _get_provider_config():
    """Get config for active provider from database."""
    active = provider_store.get_active_provider()
    if not active:
        return None  # Fall back to env vars

    # Decode API key
    if active.get('api_key'):
        active['api_key'] = provider_store.decode_api_key(active['api_key'])

    return active
```

### API Endpoints

**File:** `api_handlers.py` (extend existing) or new `provider_api_handlers.py`

```python
# GET /api/providers/status
async def providers_status_handler(request):
    """Check if wizard needed."""
    providers = provider_store.get_all_providers()
    active = provider_store.get_active_provider()
    return web.json_response({
        "needsWizard": len(providers) == 0,
        "hasProviders": len(providers) > 0,
        "activeProvider": active['name'] if active else None
    })

# GET /api/providers
async def providers_list_handler(request):
    """List all providers (API keys masked)."""
    providers = provider_store.get_all_providers()
    # Mask API keys: show only first 4 and last 4 chars
    for p in providers:
        if p.get('api_key'):
            key = p['api_key']
            p['api_key_preview'] = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "****"
            del p['api_key']
    return web.json_response({"providers": providers})

# POST /api/providers
async def providers_create_handler(request):
    """Create new provider."""
    data = await request.json()

    # Validate
    provider_type = data.get('provider_type')
    valid, error = provider_store.validate_provider_config(provider_type, data)
    if not valid:
        return web.json_response({"error": error}, status=400)

    # Encode API key
    if data.get('api_key'):
        data['api_key'] = provider_store.encode_api_key(data['api_key'])

    # Create
    provider = provider_store.create_provider(data)
    return web.json_response({"provider": provider})

# PATCH /api/providers/{name}
async def providers_update_handler(request):
    """Update provider."""
    name = request.match_info['name']
    data = await request.json()

    # Validate
    existing = provider_store.get_provider_by_name(name)
    if not existing:
        return web.json_response({"error": "Provider not found"}, status=404)

    # Encode API key if provided
    if data.get('api_key'):
        data['api_key'] = provider_store.encode_api_key(data['api_key'])

    # Update
    provider = provider_store.update_provider(name, data)
    return web.json_response({"provider": provider})

# DELETE /api/providers/{name}
async def providers_delete_handler(request):
    """Delete provider."""
    name = request.match_info['name']
    success = provider_store.delete_provider(name)
    if not success:
        return web.json_response({"error": "Provider not found"}, status=404)
    return web.json_response({"ok": True})

# POST /api/providers/{name}/activate
async def providers_activate_handler(request):
    """Set provider as active."""
    name = request.match_info['name']
    success = provider_store.set_active_provider(name)
    if not success:
        return web.json_response({"error": "Provider not found"}, status=404)

    # Reload provider at runtime
    provider_manager.reload_provider()

    return web.json_response({"ok": True, "activeProvider": name})

# POST /api/providers/{name}/test
async def providers_test_handler(request):
    """Test provider connection."""
    name = request.match_info['name']
    success, message = await provider_manager.test_provider_connection(name)
    return web.json_response({
        "success": success,
        "message": message
    })

# GET /api/providers/cli-status
async def providers_cli_status_handler(request):
    """Check CLI availability."""
    return web.json_response({
        "claude_code": _has_cli_provider_command("claude"),
        "codex": _has_cli_provider_command("codex"),
        "gemini_cli": _has_cli_provider_command("gemini")
    })
```

**Route Registration** (in `__init__.py` or separate routes module):

```python
app.router.add_get("/api/providers/status", providers_status_handler)
app.router.add_get("/api/providers", providers_list_handler)
app.router.add_post("/api/providers", providers_create_handler)
app.router.add_patch("/api/providers/{name}", providers_update_handler)
app.router.add_delete("/api/providers/{name}", providers_delete_handler)
app.router.add_post("/api/providers/{name}/activate", providers_activate_handler)
app.router.add_post("/api/providers/{name}/test", providers_test_handler)
app.router.add_get("/api/providers/cli-status", providers_cli_status_handler)
```

## Frontend Implementation

### New Components

**Directory Structure:**
```
ui/src/components/providers/
├── ProviderWizard.tsx              # Main wizard container
├── ProviderSelectionScreen.tsx     # Step 1: Choose provider
├── ProviderConfigScreen.tsx        # Step 2: Configure
├── ProviderConfirmScreen.tsx       # Step 3: Test & save
├── ProviderCard.tsx                # Provider card component
└── types.ts                        # TypeScript interfaces
```

### ProviderWizard.tsx

```typescript
interface ProviderWizardProps {
  mode: 'full-page' | 'modal'  // Adaptive display
  onComplete: () => void
}

type WizardStep = 'select' | 'configure' | 'confirm'
type ProviderType = 'openai' | 'anthropic' | 'claude_code' | 'codex' | 'gemini_cli'

const ProviderWizard = ({ mode, onComplete }: ProviderWizardProps) => {
  const [step, setStep] = useState<WizardStep>('select')
  const [selectedProvider, setSelectedProvider] = useState<ProviderType | null>(null)
  const [config, setConfig] = useState<ProviderConfig>({})

  // Wizard navigation
  const goToStep = (newStep: WizardStep) => setStep(newStep)

  // Layout wrapper based on mode
  const WrapperComponent = mode === 'modal' ? Dialog : FullPageView

  return (
    <WrapperComponent>
      {step === 'select' && <ProviderSelectionScreen onSelect={(type) => {
        setSelectedProvider(type)
        setStep('configure')
      }} />}

      {step === 'configure' && <ProviderConfigScreen
        providerType={selectedProvider!}
        initialConfig={config}
        onBack={() => setStep('select')}
        onNext={(newConfig) => {
          setConfig(newConfig)
          setStep('confirm')
        }}
      />}

      {step === 'confirm' && <ProviderConfirmScreen
        providerType={selectedProvider!}
        config={config}
        onBack={() => setStep('configure')}
        onSave={async (setAsActive, addAnother) => {
          await saveProvider(config, setAsActive)
          if (addAnother) {
            setStep('select')
            setConfig({})
          } else {
            onComplete()
          }
        }}
      />}
    </WrapperComponent>
  )
}
```

**Styling:**
- Match SOUL.md wizard exactly
- Centered card: `max-w-2xl mx-auto`
- Card styling: `rounded-lg border bg-card p-6 space-y-6`
- Buttons: shadcn `Button` component
- Inputs: shadcn `Input`, `Textarea`, `Select` components
- Dark theme support via CSS variables

### API Hook: useProviders.ts

```typescript
export const useProviders = () => {
  const [providers, setProviders] = useState<Provider[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchProviders = async () => {
    const response = await fetch('/api/providers')
    const data = await response.json()
    setProviders(data.providers)
  }

  const createProvider = async (config: ProviderConfig) => {
    const response = await fetch('/api/providers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    })
    if (!response.ok) throw new Error('Failed to create provider')
    return response.json()
  }

  const activateProvider = async (name: string) => {
    const response = await fetch(`/api/providers/${name}/activate`, {
      method: 'POST'
    })
    if (!response.ok) throw new Error('Failed to activate provider')
    return response.json()
  }

  const testConnection = async (name: string) => {
    const response = await fetch(`/api/providers/${name}/test`, {
      method: 'POST'
    })
    return response.json()
  }

  return {
    providers,
    loading,
    error,
    fetchProviders,
    createProvider,
    activateProvider,
    testConnection
  }
}
```

### App Integration: App.tsx

```typescript
function App() {
  const [needsWizard, setNeedsWizard] = useState<boolean | null>(null)
  const [showWizard, setShowWizard] = useState(false)

  useEffect(() => {
    // Check wizard status on mount
    fetch('/api/providers/status')
      .then(res => res.json())
      .then(({ needsWizard: needs }) => {
        setNeedsWizard(needs)
        setShowWizard(needs)  // Auto-show on first use
      })
      .catch(() => setNeedsWizard(false))
  }, [])

  // Loading state
  if (needsWizard === null) {
    return <div className="flex h-full items-center justify-center">
      <div className="text-muted-foreground">Loading...</div>
    </div>
  }

  // First-time wizard (full-page)
  if (showWizard && needsWizard) {
    return <ProviderWizard
      mode="full-page"
      onComplete={() => {
        setShowWizard(false)
        setNeedsWizard(false)
      }}
    />
  }

  // Normal app with optional modal wizard
  return (
    <>
      <AppContent />
      {/* Modal wizard triggered by /provider-settings */}
      {showWizard && !needsWizard && (
        <ProviderWizard
          mode="modal"
          onComplete={() => setShowWizard(false)}
        />
      )}
    </>
  )
}
```

## Slash Commands Implementation

### Frontend Commands

**File:** `ui/src/slash-commands/commands.ts`

```typescript
// Command 1: Open wizard
{
  name: 'provider-settings',
  description: 'Configure AI providers',
  usage: '/provider-settings',
  execute: (args, ctx) => {
    // Trigger wizard modal
    window.dispatchEvent(new CustomEvent('open-provider-wizard'))
    ctx.appendLocal('Opening provider settings...')
  }
}

// Command 2: Provider management (backend-handled)
{
  name: 'provider',
  description: 'Switch or list providers',
  usage: '/provider <set|list> [name]',
  execute: (args, ctx) => {
    // Don't execute locally - let backend handle it
    return false  // Message sent to backend
  }
}
```

### Backend Command Interception

**File:** `__init__.py` in `chat_api_handler`

Add command interception similar to `/skill`:

```python
async def _handle_provider_command(command_text: str) -> dict | None:
    """Handle /provider commands, return response dict or None."""
    parts = command_text.strip().split()
    if len(parts) < 2:
        return {
            "error": "Usage: /provider <set|list> [name]"
        }

    subcommand = parts[1].lower()

    if subcommand == "list":
        providers = provider_store.get_all_providers()
        active = provider_store.get_active_provider()

        # Format list
        lines = ["**Configured Providers:**\n"]
        for p in providers:
            marker = "✓" if p['name'] == active['name'] else " "
            lines.append(f"{marker} **{p['display_name']}** (`{p['name']}`)")

        return {
            "text": "\n".join(lines),
            "local": True  # Don't send to LLM
        }

    elif subcommand == "set":
        if len(parts) < 3:
            return {"error": "Usage: /provider set <name>"}

        name = parts[2]
        success = provider_store.set_active_provider(name)

        if not success:
            return {"error": f"Provider '{name}' not found"}

        # Reload provider
        provider_manager.reload_provider()

        return {
            "text": f"✓ Switched to provider: **{name}**\n\nContinuing conversation with new provider.",
            "local": True
        }

    else:
        return {"error": f"Unknown subcommand: {subcommand}"}

# In chat_api_handler, before LLM call:
user_message = messages[-1]['content']
if isinstance(user_message, str) and user_message.startswith("/provider "):
    response = await _handle_provider_command(user_message)
    if response:
        # Return response as SSE stream
        return stream_local_response(response)
```

## Implementation Order

### Phase 1: Database Foundation ✓
1. Create `provider_store.py` with schema and CRUD
2. Add SQLite initialization on startup
3. Implement validation and encoding functions
4. Write unit tests for provider store

**Files:**
- `provider_store.py` (new)
- `test_provider_store.py` (new, optional)

### Phase 2: Backend API ✓
1. Create `provider_manager.py` for runtime management
2. Implement API endpoints in `api_handlers.py`
3. Add route registration in `__init__.py`
4. Refactor provider initialization to check DB first
5. Implement connection testing

**Files:**
- `provider_manager.py` (new)
- `api_handlers.py` (modify)
- `__init__.py` (modify provider init logic, add routes)

### Phase 3: Frontend Wizard Components ✓
1. Create `ProviderWizard.tsx` with step management
2. Build `ProviderSelectionScreen.tsx`
3. Build `ProviderConfigScreen.tsx` with dynamic forms
4. Build `ProviderConfirmScreen.tsx` with testing
5. Create `useProviders.ts` hook
6. Style components matching SOUL.md

**Files:**
- `ui/src/components/providers/ProviderWizard.tsx` (new)
- `ui/src/components/providers/ProviderSelectionScreen.tsx` (new)
- `ui/src/components/providers/ProviderConfigScreen.tsx` (new)
- `ui/src/components/providers/ProviderConfirmScreen.tsx` (new)
- `ui/src/components/providers/types.ts` (new)
- `ui/src/hooks/useProviders.ts` (new)

### Phase 4: App Integration ✓
1. Add wizard detection in `App.tsx`
2. Implement full-page mode for first-time
3. Implement modal mode for `/provider-settings`
4. Test wizard flow end-to-end

**Files:**
- `ui/src/App.tsx` (modify)
- `ui/src/components/providers/ProviderWizard.tsx` (add modal support)

### Phase 5: Slash Commands ✓
1. Add `/provider-settings` to frontend commands
2. Implement `/provider` backend handler
3. Wire wizard modal trigger
4. Test command flow

**Files:**
- `ui/src/slash-commands/commands.ts` (modify)
- `__init__.py` (add command handler)

### Phase 6: Testing & Polish ✓
1. Test all 5 provider types
2. Test provider switching at runtime
3. Test validation and error messages
4. Test CLI detection
5. Verify styling matches SOUL.md
6. Add loading states and animations

## Critical Files Summary

### New Backend Files:
- `/home/victor/AI/Comfy/ComfyUI/custom_nodes/ComfyUI_ComfyAssistant/provider_store.py`
- `/home/victor/AI/Comfy/ComfyUI/custom_nodes/ComfyUI_ComfyAssistant/provider_manager.py`
- `/home/victor/AI/Comfy/ComfyUI/custom_nodes/ComfyUI_ComfyAssistant/user_context/providers.db`

### Modified Backend Files:
- `/home/victor/AI/Comfy/ComfyUI/custom_nodes/ComfyUI_ComfyAssistant/__init__.py` (provider init refactor, routes, command handler)
- `/home/victor/AI/Comfy/ComfyUI/custom_nodes/ComfyUI_ComfyAssistant/api_handlers.py` (add provider endpoints)

### New Frontend Files:
- `/home/victor/AI/Comfy/ComfyUI/custom_nodes/ComfyUI_ComfyAssistant/ui/src/components/providers/ProviderWizard.tsx`
- `/home/victor/AI/Comfy/ComfyUI/custom_nodes/ComfyUI_ComfyAssistant/ui/src/components/providers/ProviderSelectionScreen.tsx`
- `/home/victor/AI/Comfy/ComfyUI/custom_nodes/ComfyUI_ComfyAssistant/ui/src/components/providers/ProviderConfigScreen.tsx`
- `/home/victor/AI/Comfy/ComfyUI/custom_nodes/ComfyUI_ComfyAssistant/ui/src/components/providers/ProviderConfirmScreen.tsx`
- `/home/victor/AI/Comfy/ComfyUI/custom_nodes/ComfyUI_ComfyAssistant/ui/src/components/providers/types.ts`
- `/home/victor/AI/Comfy/ComfyUI/custom_nodes/ComfyUI_ComfyAssistant/ui/src/hooks/useProviders.ts`

### Modified Frontend Files:
- `/home/victor/AI/Comfy/ComfyUI/custom_nodes/ComfyUI_ComfyAssistant/ui/src/App.tsx` (wizard detection)
- `/home/victor/AI/Comfy/ComfyUI/custom_nodes/ComfyUI_ComfyAssistant/ui/src/slash-commands/commands.ts` (add commands)

## Key Design Decisions

1. **No Migration Logic**: User will manually configure providers through wizard and delete `.env` file
2. **CLI Providers**: One config per type (name = provider_type), enforced by database constraint
3. **API Providers**: Multiple configs allowed with custom names (e.g., "openai-groq", "anthropic-opus")
4. **Adaptive UI**: Full-page wizard on first use, modal dialog for `/provider-settings`
5. **Runtime Switching**: Provider can be switched without restart via `/provider set <name>`
6. **Security**: Base64 encoding for API keys (suitable for local deployment)
7. **Styling**: Exact match to SOUL.md wizard (centered card, Tailwind CSS, shadcn components)
8. **Provider Switching Behavior**: Conversation continues with new provider (no forced session reset)

## Verification Steps

After implementation:

1. **First-Time Flow**:
   - Delete `providers.db`
   - Open Assistant tab
   - Verify wizard shows automatically
   - Configure a provider
   - Verify chat loads successfully

2. **Provider Management**:
   - Add multiple OpenAI configs (different API keys)
   - Add Anthropic config
   - Run `/provider list` - verify all shown
   - Run `/provider set <name>` - verify switch works
   - Send message - verify new provider responds

3. **CLI Providers**:
   - Configure `claude_code` (if available)
   - Verify CLI detection works
   - Test connection
   - Switch to CLI provider
   - Send message - verify works

4. **Wizard Styling**:
   - Compare side-by-side with SOUL.md wizard
   - Verify matching layout, spacing, colors
   - Test dark mode
   - Verify responsive design

5. **Error Handling**:
   - Try invalid API key - verify error shown
   - Try non-existent CLI path - verify validation
   - Try connection test with bad config - verify message
   - Try switching to non-existent provider - verify error
