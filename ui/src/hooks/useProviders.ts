import { useCallback, useState } from 'react'

import type {
  ProviderConfig,
  ProviderRecord,
  ProvidersCliStatus,
  ProvidersStatus
} from '@/components/providers/types'

const JSON_HEADERS = { 'Content-Type': 'application/json' }

async function parseApiError(response: Response): Promise<string> {
  const body = await response.json().catch(() => null)
  return body?.error || response.statusText || 'Request failed'
}

export function useProviders() {
  const [providers, setProviders] = useState<ProviderRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchStatus = useCallback(async (): Promise<ProvidersStatus> => {
    const response = await fetch('/api/providers/status')
    if (!response.ok) {
      throw new Error(await parseApiError(response))
    }
    return response.json()
  }, [])

  const fetchProviders = useCallback(async (): Promise<ProviderRecord[]> => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/providers')
      if (!response.ok) {
        throw new Error(await parseApiError(response))
      }
      const data = (await response.json()) as { providers: ProviderRecord[] }
      setProviders(data.providers || [])
      return data.providers || []
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to load providers'
      setError(message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const createProvider = useCallback(
    async (config: ProviderConfig) => {
      const response = await fetch('/api/providers', {
        method: 'POST',
        headers: JSON_HEADERS,
        body: JSON.stringify(config)
      })
      if (!response.ok) {
        throw new Error(await parseApiError(response))
      }
      const data = await response.json()
      await fetchProviders()
      return data
    },
    [fetchProviders]
  )

  const updateProvider = useCallback(
    async (name: string, config: Partial<ProviderConfig>) => {
      const response = await fetch(
        `/api/providers/${encodeURIComponent(name)}`,
        {
          method: 'PATCH',
          headers: JSON_HEADERS,
          body: JSON.stringify(config)
        }
      )
      if (!response.ok) {
        throw new Error(await parseApiError(response))
      }
      const data = await response.json()
      await fetchProviders()
      return data
    },
    [fetchProviders]
  )

  const activateProvider = useCallback(
    async (name: string) => {
      const response = await fetch(
        `/api/providers/${encodeURIComponent(name)}/activate`,
        {
          method: 'POST'
        }
      )
      if (!response.ok) {
        throw new Error(await parseApiError(response))
      }
      const data = await response.json()
      await fetchProviders()
      return data
    },
    [fetchProviders]
  )

  const testConnection = useCallback(async (name: string) => {
    const response = await fetch(
      `/api/providers/${encodeURIComponent(name)}/test`,
      {
        method: 'POST'
      }
    )
    if (!response.ok) {
      throw new Error(await parseApiError(response))
    }
    return response.json() as Promise<{ success: boolean; message: string }>
  }, [])

  const testConfig = useCallback(async (config: ProviderConfig) => {
    const response = await fetch('/api/providers/test-config', {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify(config)
    })
    if (!response.ok) {
      throw new Error(await parseApiError(response))
    }
    return response.json() as Promise<{ success: boolean; message: string }>
  }, [])

  const fetchCliStatus = useCallback(async (): Promise<ProvidersCliStatus> => {
    const response = await fetch('/api/providers/cli-status')
    if (!response.ok) {
      throw new Error(await parseApiError(response))
    }
    return response.json()
  }, [])

  return {
    providers,
    loading,
    error,
    fetchStatus,
    fetchProviders,
    createProvider,
    updateProvider,
    activateProvider,
    testConnection,
    testConfig,
    fetchCliStatus
  }
}
