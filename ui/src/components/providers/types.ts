export type ProviderType =
  | 'openai'
  | 'anthropic'
  | 'claude_code'
  | 'codex'
  | 'gemini_cli'

export type WizardStep = 'select' | 'configure' | 'confirm'

export interface ProviderConfig {
  provider_type: ProviderType
  name: string
  display_name: string
  api_key?: string
  base_url?: string
  model?: string
  max_tokens?: number
  cli_command?: string
  cli_model?: string
  timeout_seconds?: number
  is_active?: boolean
}

export interface ProviderRecord {
  id: number
  provider_type: ProviderType
  name: string
  display_name: string
  base_url?: string | null
  model?: string | null
  max_tokens?: number | null
  cli_command?: string | null
  cli_model?: string | null
  timeout_seconds?: number | null
  is_active: 0 | 1
  created_at: string
  updated_at: string
  api_key_preview?: string
}

export interface ProvidersStatus {
  needsWizard: boolean
  hasProviders: boolean
  activeProvider: string | null
}

export interface CliProviderStatus {
  available: boolean
  detectedPath: string | null
}

export type ProvidersCliStatus = Record<
  'claude_code' | 'codex' | 'gemini_cli',
  CliProviderStatus
>

export const OPEN_PROVIDER_WIZARD_EVENT = 'comfy-assistant:open-provider-wizard'
