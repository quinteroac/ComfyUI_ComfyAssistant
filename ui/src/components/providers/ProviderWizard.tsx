import { useEffect, useState } from 'react'

import { ProviderConfigScreen } from '@/components/providers/ProviderConfigScreen'
import { ProviderConfirmScreen } from '@/components/providers/ProviderConfirmScreen'
import { ProviderSelectionScreen } from '@/components/providers/ProviderSelectionScreen'
import type {
  ProviderConfig,
  ProviderType,
  ProvidersCliStatus,
  WizardStep
} from '@/components/providers/types'
import { useProviders } from '@/hooks/useProviders'

interface ProviderWizardProps {
  mode: 'full-page' | 'modal'
  onComplete: () => void
  onClose?: () => void
}

function WizardBody({
  mode,
  step,
  selectedProvider,
  config,
  cliStatus,
  setStep,
  setSelectedProvider,
  setConfig,
  onComplete
}: {
  mode: 'full-page' | 'modal'
  step: WizardStep
  selectedProvider: ProviderType | null
  config: ProviderConfig | null
  cliStatus: ProvidersCliStatus | null
  setStep: (step: WizardStep) => void
  setSelectedProvider: (providerType: ProviderType | null) => void
  setConfig: (config: ProviderConfig | null) => void
  onComplete: () => void
}) {
  const { createProvider, updateProvider, activateProvider, testConfig } =
    useProviders()

  if (step === 'select') {
    return (
      <ProviderSelectionScreen
        cliStatus={cliStatus}
        onSelect={(providerType) => {
          setSelectedProvider(providerType)
          setStep('configure')
        }}
      />
    )
  }

  if (!selectedProvider) return null

  if (step === 'configure') {
    return (
      <ProviderConfigScreen
        providerType={selectedProvider}
        initialConfig={config || {}}
        cliStatus={cliStatus}
        onBack={() => {
          setStep('select')
          if (mode === 'modal') {
            setConfig(null)
          }
        }}
        onNext={(nextConfig) => {
          setConfig(nextConfig)
          setStep('confirm')
        }}
      />
    )
  }

  if (!config) return null

  return (
    <ProviderConfirmScreen
      providerType={selectedProvider}
      config={config}
      onBack={() => setStep('configure')}
      onTest={() => testConfig(config)}
      onSave={async ({ setAsActive, addAnother }) => {
        const payload = { ...config, is_active: setAsActive }
        try {
          await createProvider(payload)
        } catch (error) {
          const message = error instanceof Error ? error.message : ''
          if (message.includes('UNIQUE constraint failed: providers.name')) {
            await updateProvider(payload.name, payload)
          } else {
            throw error
          }
        }
        if (setAsActive && payload.name) {
          await activateProvider(payload.name)
        }

        if (addAnother) {
          setStep('select')
          setSelectedProvider(null)
          setConfig(null)
          return
        }
        onComplete()
      }}
    />
  )
}

export function ProviderWizard({
  mode,
  onComplete,
}: ProviderWizardProps) {
  const { fetchCliStatus } = useProviders()
  const [step, setStep] = useState<WizardStep>('select')
  const [selectedProvider, setSelectedProvider] = useState<ProviderType | null>(
    null
  )
  const [config, setConfig] = useState<ProviderConfig | null>(null)
  const [cliStatus, setCliStatus] = useState<ProvidersCliStatus | null>(null)

  useEffect(() => {
    fetchCliStatus()
      .then(setCliStatus)
      .catch(() => setCliStatus(null))
  }, [fetchCliStatus])

  return (
    <div className="flex h-full min-h-0 flex-col items-center justify-center overflow-auto p-6">
      <div className="w-full max-w-2xl">
        <div className="w-full space-y-6 rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
          <WizardBody
            mode={mode}
            step={step}
            selectedProvider={selectedProvider}
            config={config}
            cliStatus={cliStatus}
            setStep={setStep}
            setSelectedProvider={setSelectedProvider}
            setConfig={setConfig}
            onComplete={onComplete}
          />
        </div>
      </div>
    </div>
  )
}
