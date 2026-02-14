import { AlertTriangleIcon, CheckCircle2Icon } from 'lucide-react'

import type { ProviderType } from '@/components/providers/types'
import { Button } from '@/components/ui/button'

interface ProviderCardProps {
  providerType: ProviderType
  title: string
  description: string
  isCli: boolean
  cliAvailable?: boolean
  onConfigure: (providerType: ProviderType) => void
}

export function ProviderCard({
  providerType,
  title,
  description,
  isCli,
  cliAvailable,
  onConfigure
}: ProviderCardProps) {
  return (
    <div className="rounded-lg border bg-card p-4 text-card-foreground shadow-sm">
      <div className="space-y-1">
        <h3 className="text-base font-semibold">{title}</h3>
        <p className="text-muted-foreground text-sm">{description}</p>
      </div>

      {isCli && (
        <div className="mt-3 text-xs">
          {cliAvailable ? (
            <div className="text-emerald-600 flex items-center gap-1">
              <CheckCircle2Icon className="size-3.5" /> CLI available
            </div>
          ) : (
            <div className="text-amber-600 flex items-center gap-1">
              <AlertTriangleIcon className="size-3.5" /> CLI not found
            </div>
          )}
        </div>
      )}

      <div className="mt-4">
        <Button className="w-full" onClick={() => onConfigure(providerType)}>
          Configure
        </Button>
      </div>
    </div>
  )
}
