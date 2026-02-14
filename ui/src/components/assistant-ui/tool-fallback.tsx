'use client'

import {
  type ToolCallMessagePartComponent,
  type ToolCallMessagePartStatus,
  useScrollLock
} from '@assistant-ui/react'
import {
  AlertCircleIcon,
  CheckIcon,
  ChevronDownIcon,
  LoaderIcon,
  XCircleIcon
} from 'lucide-react'
import { memo, useCallback, useRef, useState } from 'react'

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger
} from '@/components/ui/collapsible'
import { cn } from '@/lib/utils'

const ANIMATION_DURATION = 200

export type ToolFallbackRootProps = Omit<
  React.ComponentProps<typeof Collapsible>,
  'open' | 'onOpenChange'
> & {
  open?: boolean
  onOpenChange?: (open: boolean) => void
  defaultOpen?: boolean
}

function ToolFallbackRoot({
  className,
  open: controlledOpen,
  onOpenChange: controlledOnOpenChange,
  defaultOpen = false,
  children,
  ...props
}: ToolFallbackRootProps) {
  const collapsibleRef = useRef<HTMLDivElement>(null)
  const [uncontrolledOpen, setUncontrolledOpen] = useState(defaultOpen)
  const lockScroll = useScrollLock(collapsibleRef, ANIMATION_DURATION)

  const isControlled = controlledOpen !== undefined
  const isOpen = isControlled ? controlledOpen : uncontrolledOpen

  const handleOpenChange = useCallback(
    (open: boolean) => {
      if (!open) {
        lockScroll()
      }
      if (!isControlled) {
        setUncontrolledOpen(open)
      }
      controlledOnOpenChange?.(open)
    },
    [lockScroll, isControlled, controlledOnOpenChange]
  )

  return (
    <Collapsible
      ref={collapsibleRef}
      data-slot="tool-fallback-root"
      open={isOpen}
      onOpenChange={handleOpenChange}
      className={cn(
        'aui-tool-fallback-root comfy-assistant-tool-line group/tool-fallback-root w-full py-0.5',
        className
      )}
      style={
        {
          '--animation-duration': `${ANIMATION_DURATION}ms`,
          background: 'transparent',
          border: 'none',
          borderRadius: 0,
          padding: '2px 0',
          boxShadow: 'none'
        } as React.CSSProperties
      }
      {...props}
    >
      {children}
    </Collapsible>
  )
}

type ToolStatus = ToolCallMessagePartStatus['type']

const statusIconMap: Record<ToolStatus, React.ElementType> = {
  running: LoaderIcon,
  complete: CheckIcon,
  incomplete: XCircleIcon,
  'requires-action': AlertCircleIcon
}

function ToolFallbackTrigger({
  toolName,
  status,
  className,
  ...props
}: React.ComponentProps<typeof CollapsibleTrigger> & {
  toolName: string
  status?: ToolCallMessagePartStatus
}) {
  const statusType = status?.type ?? 'complete'
  const isRunning = statusType === 'running'
  const isCancelled =
    status?.type === 'incomplete' && status.reason === 'cancelled'

  const Icon = statusIconMap[statusType]

  return (
    <CollapsibleTrigger
      data-slot="tool-fallback-trigger"
      className={cn(
        'aui-tool-fallback-trigger group/trigger flex w-full items-center gap-1.5 transition-colors',
        className
      )}
      {...props}
    >
      <span
        className="aui-tool-fallback-prefix shrink-0 select-none"
        style={{ color: 'hsl(var(--terminal-dim))' }}
        aria-hidden
      >
        ›
      </span>
      <Icon
        data-slot="tool-fallback-trigger-icon"
        className={cn(
          'aui-tool-fallback-trigger-icon size-3.5 shrink-0',
          isCancelled && 'text-muted-foreground',
          isRunning && 'animate-spin'
        )}
      />
      <span
        data-slot="tool-fallback-trigger-label"
        className={cn(
          'aui-tool-fallback-trigger-label-wrapper relative inline-block grow text-left truncate',
          isCancelled && 'text-muted-foreground line-through'
        )}
      >
        <span>{toolName}</span>
        {isRunning && (
          <span
            aria-hidden
            data-slot="tool-fallback-trigger-shimmer"
            className="aui-tool-fallback-trigger-shimmer shimmer pointer-events-none absolute inset-0 motion-reduce:animate-none"
          >
            {toolName}
          </span>
        )}
      </span>
      <ChevronDownIcon
        data-slot="tool-fallback-trigger-chevron"
        className={cn(
          'aui-tool-fallback-trigger-chevron size-3.5 shrink-0 opacity-70',
          'transition-transform duration-(--animation-duration) ease-out',
          'group-data-[state=closed]/trigger:-rotate-90',
          'group-data-[state=open]/trigger:rotate-0'
        )}
      />
    </CollapsibleTrigger>
  )
}

function ToolFallbackContent({
  className,
  children,
  ...props
}: React.ComponentProps<typeof CollapsibleContent>) {
  return (
    <CollapsibleContent
      data-slot="tool-fallback-content"
      className={cn(
        'aui-tool-fallback-content relative overflow-hidden outline-none',
        'group/collapsible-content ease-out',
        'data-[state=closed]:animate-collapsible-up',
        'data-[state=open]:animate-collapsible-down',
        'data-[state=closed]:fill-mode-forwards',
        'data-[state=closed]:pointer-events-none',
        'data-[state=open]:duration-(--animation-duration)',
        'data-[state=closed]:duration-(--animation-duration)',
        className
      )}
      {...props}
    >
      <div className="aui-tool-fallback-detail mt-1 flex flex-col gap-1 pt-1.5 pl-2">
        {children}
      </div>
    </CollapsibleContent>
  )
}

function ToolFallbackArgs({
  argsText,
  className,
  ...props
}: React.ComponentProps<'div'> & {
  argsText?: string
}) {
  if (!argsText) return null

  return (
    <div
      data-slot="tool-fallback-args"
      className={cn('aui-tool-fallback-args', className)}
      {...props}
    >
      <pre className="aui-tool-fallback-args-value whitespace-pre-wrap break-words">
        {argsText}
      </pre>
    </div>
  )
}

function ToolFallbackResult({
  result,
  className,
  ...props
}: React.ComponentProps<'div'> & {
  result?: unknown
}) {
  if (result === undefined) return null

  return (
    <div
      data-slot="tool-fallback-result"
      className={cn('aui-tool-fallback-result pt-1', className)}
      {...props}
    >
      <p className="aui-tool-fallback-result-header text-muted-foreground font-medium text-xs uppercase tracking-wide">
        Result
      </p>
      <pre className="aui-tool-fallback-result-content mt-0.5 whitespace-pre-wrap break-words">
        {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
      </pre>
    </div>
  )
}

function ToolFallbackError({
  status,
  className,
  ...props
}: React.ComponentProps<'div'> & {
  status?: ToolCallMessagePartStatus
}) {
  if (status?.type !== 'incomplete') return null

  const error = status.error
  const errorText = error
    ? typeof error === 'string'
      ? error
      : JSON.stringify(error)
    : null

  if (!errorText) return null

  const isCancelled = status.reason === 'cancelled'
  const headerText = isCancelled ? 'Cancelled reason:' : 'Error:'

  return (
    <div
      data-slot="tool-fallback-error"
      className={cn('aui-tool-fallback-error', className)}
      {...props}
    >
      <p className="aui-tool-fallback-error-header font-medium text-muted-foreground text-xs uppercase tracking-wide">
        {headerText}
      </p>
      <p className="aui-tool-fallback-error-reason mt-0.5 text-muted-foreground text-sm">
        {errorText}
      </p>
    </div>
  )
}

const ToolFallbackImpl: ToolCallMessagePartComponent = ({
  toolName,
  argsText,
  result,
  status
}) => {
  const isCancelled =
    status?.type === 'incomplete' && status.reason === 'cancelled'

  return (
    <ToolFallbackRoot
      className={cn(isCancelled && 'opacity-70')}
    >
      <ToolFallbackTrigger toolName={toolName} status={status} />
      <ToolFallbackContent>
        <ToolFallbackError status={status} />
        <ToolFallbackArgs
          argsText={argsText}
          className={cn(isCancelled && 'opacity-60')}
        />
        {!isCancelled && <ToolFallbackResult result={result} />}
      </ToolFallbackContent>
    </ToolFallbackRoot>
  )
}

const ToolFallback = memo(
  ToolFallbackImpl
) as unknown as ToolCallMessagePartComponent & {
  Root: typeof ToolFallbackRoot
  Trigger: typeof ToolFallbackTrigger
  Content: typeof ToolFallbackContent
  Args: typeof ToolFallbackArgs
  Result: typeof ToolFallbackResult
  Error: typeof ToolFallbackError
}

ToolFallback.displayName = 'ToolFallback'
ToolFallback.Root = ToolFallbackRoot
ToolFallback.Trigger = ToolFallbackTrigger
ToolFallback.Content = ToolFallbackContent
ToolFallback.Args = ToolFallbackArgs
ToolFallback.Result = ToolFallbackResult
ToolFallback.Error = ToolFallbackError

export {
  ToolFallback,
  ToolFallbackRoot,
  ToolFallbackTrigger,
  ToolFallbackContent,
  ToolFallbackArgs,
  ToolFallbackResult,
  ToolFallbackError
}
