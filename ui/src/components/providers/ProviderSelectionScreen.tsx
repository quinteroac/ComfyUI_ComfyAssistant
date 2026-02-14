import { ProviderCard } from '@/components/providers/ProviderCard'
import type {
  ProviderType,
  ProvidersCliStatus
} from '@/components/providers/types'

const PROVIDERS: Array<{
  type: ProviderType
  title: string
  description: string
  isCli: boolean
}> = [
  {
    type: 'openai',
    title: 'OpenAI',
    description: 'OpenAI-compatible API provider configuration.',
    isCli: false
  },
  {
    type: 'anthropic',
    title: 'Anthropic',
    description: 'Direct Anthropic Messages API configuration.',
    isCli: false
  },
  {
    type: 'claude_code',
    title: 'Claude Code',
    description: 'Use local Claude Code CLI authentication.',
    isCli: true
  },
  {
    type: 'codex',
    title: 'Codex',
    description: 'Use local Codex CLI for chat + tools.',
    isCli: true
  },
  {
    type: 'gemini_cli',
    title: 'Gemini CLI',
    description: 'Use local Gemini CLI for chat + tools.',
    isCli: true
  }
]

interface ProviderSelectionScreenProps {
  cliStatus: ProvidersCliStatus | null
  onSelect: (providerType: ProviderType) => void
}

export function ProviderSelectionScreen({
  cliStatus,
  onSelect
}: ProviderSelectionScreenProps) {
  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-xl font-semibold">Configure Your AI Provider</h2>
        <p className="text-muted-foreground text-sm">
          Choose a provider to get started.
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {PROVIDERS.map((provider) => {
          const cliAvailable = provider.isCli
            ? cliStatus?.[
                provider.type as 'claude_code' | 'codex' | 'gemini_cli'
              ]?.available
            : undefined
          return (
            <ProviderCard
              key={provider.type}
              providerType={provider.type}
              title={provider.title}
              description={provider.description}
              isCli={provider.isCli}
              cliAvailable={cliAvailable}
              onConfigure={onSelect}
            />
          )
        })}
      </div>
    </div>
  )
}
