import { useState } from 'react'

import type { ProviderConfig, ProviderType } from '@/components/providers/types'
import { Button } from '@/components/ui/button'

interface ProviderConfirmScreenProps {
  providerType: ProviderType
  config: ProviderConfig
  onBack: () => void
  onSave: (opts: { setAsActive: boolean; addAnother: boolean }) => Promise<void>
  onTest: () => Promise<{ success: boolean; message: string }>
}

export function ProviderConfirmScreen({
  providerType,
  config,
  onBack,
  onSave,
  onTest
}: ProviderConfirmScreenProps) {
  const [setAsActive, setSetAsActive] = useState(true)
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{
    success: boolean
    message: string
  } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleTest = async () => {
    setTesting(true)
    setError(null)
    try {
      const result = await onTest()
      setTestResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection test failed')
      setTestResult(null)
    } finally {
      setTesting(false)
    }
  }

  const handleSave = async (addAnother: boolean) => {
    setLoading(true)
    setError(null)
    try {
      await onSave({ setAsActive, addAnother })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save provider')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-xl font-semibold">Confirm Configuration</h2>
        <p className="text-muted-foreground text-sm">
          Review and test your {providerType.replace('_', ' ')} configuration.
        </p>
      </div>

      <div className="space-y-2 rounded-lg border bg-background p-4 text-sm">
        <p>
          <span className="font-medium">Name:</span> {config.name}
        </p>
        <p>
          <span className="font-medium">Display name:</span>{' '}
          {config.display_name}
        </p>
        {config.base_url && (
          <p>
            <span className="font-medium">Base URL:</span> {config.base_url}
          </p>
        )}
        {config.model && (
          <p>
            <span className="font-medium">Model:</span> {config.model}
          </p>
        )}
        {config.cli_command && (
          <p>
            <span className="font-medium">CLI command:</span>{' '}
            {config.cli_command}
          </p>
        )}
        {config.timeout_seconds && (
          <p>
            <span className="font-medium">Timeout:</span>{' '}
            {config.timeout_seconds}s
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Button
          variant="outline"
          onClick={handleTest}
          disabled={testing || loading}
        >
          {testing ? 'Testing…' : 'Test Connection'}
        </Button>
        {testResult && (
          <p
            className={
              testResult.success
                ? 'text-emerald-600 text-sm'
                : 'text-destructive text-sm'
            }
          >
            {testResult.message}
          </p>
        )}
      </div>

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={setAsActive}
          onChange={(e) => setSetAsActive(e.target.checked)}
        />
        Set as active provider
      </label>

      {error && <p className="text-destructive text-sm">{error}</p>}

      <div className="flex flex-wrap gap-2">
        <Button variant="outline" onClick={onBack} disabled={loading}>
          Back
        </Button>
        <Button onClick={() => handleSave(false)} disabled={loading}>
          {loading ? 'Saving…' : 'Save & Finish'}
        </Button>
        <Button
          variant="outline"
          onClick={() => handleSave(true)}
          disabled={loading}
        >
          Save & Add Another
        </Button>
      </div>
    </div>
  )
}
