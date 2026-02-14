import { useEffect, useMemo, useState } from 'react'

import type {
  ProviderConfig,
  ProviderType,
  ProvidersCliStatus
} from '@/components/providers/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const DEFAULTS = {
  openai: {
    base_url: 'https://api.openai.com/v1',
    model: 'gpt-4o'
  },
  anthropic: {
    base_url: 'https://api.anthropic.com',
    model: 'claude-sonnet-4-5',
    max_tokens: 4096
  },
  claude_code: {
    display_name: 'Claude Code',
    cli_command: 'claude',
    timeout_seconds: 180
  },
  codex: {
    display_name: 'Codex',
    cli_command: 'codex',
    timeout_seconds: 180
  },
  gemini_cli: {
    display_name: 'Gemini CLI',
    cli_command: 'gemini',
    timeout_seconds: 180
  }
}

function slugify(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 63)
}

interface ProviderConfigScreenProps {
  providerType: ProviderType
  initialConfig: Partial<ProviderConfig>
  cliStatus: ProvidersCliStatus | null
  onBack: () => void
  onNext: (config: ProviderConfig) => void
}

export function ProviderConfigScreen({
  providerType,
  initialConfig,
  cliStatus,
  onBack,
  onNext
}: ProviderConfigScreenProps) {
  const isApiProvider =
    providerType === 'openai' || providerType === 'anthropic'

  const detectedCliPath = useMemo(() => {
    if (!cliStatus) return null
    if (providerType === 'claude_code')
      return cliStatus.claude_code.detectedPath
    if (providerType === 'codex') return cliStatus.codex.detectedPath
    if (providerType === 'gemini_cli') return cliStatus.gemini_cli.detectedPath
    return null
  }, [cliStatus, providerType])

  const [displayName, setDisplayName] = useState(
    initialConfig.display_name ||
      (providerType === 'openai'
        ? 'OpenAI'
        : providerType === 'anthropic'
          ? 'Anthropic'
          : DEFAULTS[providerType].display_name)
  )
  const [name, setName] = useState(
    initialConfig.name || (isApiProvider ? '' : providerType)
  )
  const [nameTouched, setNameTouched] = useState(Boolean(initialConfig.name))
  const [apiKey, setApiKey] = useState(initialConfig.api_key || '')
  const [baseUrl, setBaseUrl] = useState(
    initialConfig.base_url ||
      (isApiProvider ? DEFAULTS[providerType].base_url : '')
  )
  const [model, setModel] = useState(
    initialConfig.model ||
      (providerType === 'openai' || providerType === 'anthropic'
        ? DEFAULTS[providerType].model
        : '')
  )
  const [maxTokens, setMaxTokens] = useState(
    initialConfig.max_tokens ||
      (providerType === 'anthropic' ? DEFAULTS.anthropic.max_tokens : 4096)
  )
  const [cliCommand, setCliCommand] = useState(
    initialConfig.cli_command ||
      detectedCliPath ||
      (!isApiProvider ? DEFAULTS[providerType].cli_command : '')
  )
  const [cliModel, setCliModel] = useState(initialConfig.cli_model || '')
  const [timeoutSeconds, setTimeoutSeconds] = useState(
    initialConfig.timeout_seconds ||
      (!isApiProvider ? DEFAULTS[providerType].timeout_seconds : 180)
  )
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isApiProvider && !nameTouched) {
      setName(slugify(displayName))
    }
  }, [displayName, isApiProvider, nameTouched])

  useEffect(() => {
    if (!isApiProvider && detectedCliPath && !initialConfig.cli_command) {
      setCliCommand(detectedCliPath)
    }
  }, [detectedCliPath, initialConfig.cli_command, isApiProvider])

  const validate = (): string | null => {
    if (!displayName.trim()) return 'Display name is required.'

    if (isApiProvider) {
      if (!name.trim()) return 'Name is required.'
      if (!/^[a-z0-9][a-z0-9_-]{1,62}$/.test(name.trim())) {
        return 'Name must match: lowercase letters, numbers, underscore, hyphen.'
      }
      if (apiKey.trim().length < 20) {
        return 'API key must have at least 20 characters.'
      }
      if (baseUrl.trim() && !/^https?:\/\//.test(baseUrl.trim())) {
        return 'Base URL must start with http:// or https://'
      }
      if (providerType === 'anthropic' && maxTokens < 64) {
        return 'Max tokens must be at least 64.'
      }
      return null
    }

    if (!cliCommand.trim()) return 'CLI command is required.'
    if (timeoutSeconds < 10) return 'Timeout must be at least 10 seconds.'
    return null
  }

  const handleNext = () => {
    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }

    setError(null)

    if (isApiProvider) {
      onNext({
        provider_type: providerType,
        name: name.trim(),
        display_name: displayName.trim(),
        api_key: apiKey.trim(),
        base_url: baseUrl.trim(),
        model: model.trim(),
        max_tokens: providerType === 'anthropic' ? Number(maxTokens) : undefined
      })
      return
    }

    onNext({
      provider_type: providerType,
      name: providerType,
      display_name: displayName.trim(),
      cli_command: cliCommand.trim(),
      cli_model: cliModel.trim(),
      timeout_seconds: Number(timeoutSeconds)
    })
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-xl font-semibold">Provider Configuration</h2>
        <p className="text-muted-foreground text-sm">
          Configure {providerType.replace('_', ' ')} settings.
        </p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Display Name</label>
          <Input
            placeholder="Human-readable provider name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />
        </div>

        {isApiProvider ? (
          <>
            <div className="space-y-2">
              <label className="text-sm font-medium">Name</label>
              <Input
                placeholder="unique-provider-name"
                value={name}
                onChange={(e) => {
                  setNameTouched(true)
                  setName(slugify(e.target.value))
                }}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">API Key</label>
              <Input
                type="password"
                placeholder="Paste API key"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Base URL</label>
              <Input
                placeholder="https://api.example.com/v1"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Model</label>
              <Input
                placeholder="model-name"
                value={model}
                onChange={(e) => setModel(e.target.value)}
              />
            </div>

            {providerType === 'anthropic' && (
              <div className="space-y-2">
                <label className="text-sm font-medium">Max Tokens</label>
                <Input
                  type="number"
                  min={64}
                  step={1}
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(Number(e.target.value) || 0)}
                />
              </div>
            )}
          </>
        ) : (
          <>
            <div className="space-y-2">
              <label className="text-sm font-medium">Name</label>
              <Input value={providerType} readOnly className="opacity-80" />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">CLI Command</label>
              <Input
                placeholder="Path or command in PATH"
                value={cliCommand}
                onChange={(e) => setCliCommand(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">
                CLI Model (optional)
              </label>
              <Input
                placeholder="Optional model selection"
                value={cliModel}
                onChange={(e) => setCliModel(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Timeout Seconds</label>
              <Input
                type="number"
                min={10}
                step={1}
                value={timeoutSeconds}
                onChange={(e) => setTimeoutSeconds(Number(e.target.value) || 0)}
              />
            </div>
          </>
        )}
      </div>

      {error && <p className="text-destructive text-sm">{error}</p>}

      <div className="flex gap-2">
        <Button variant="outline" onClick={onBack}>
          Back
        </Button>
        <Button onClick={handleNext}>Next</Button>
      </div>
    </div>
  )
}
