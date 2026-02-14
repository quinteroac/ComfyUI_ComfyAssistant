/**
 * Main application component with agentic tools.
 *
 * Tools are registered via useAssistantTool (in useComfyTools) into the
 * runtime's ModelContext. When the LLM returns tool-call parts, the runtime
 * automatically executes the matching tool, feeds the result back through
 * addToolResult, and resubmits for the next LLM response — forming a
 * proper agentic loop without any text-based hacks.
 *
 * Phase 1: optional first-time onboarding; on first load we check
 * /api/user-context/status and show onboarding UI if needed.
 */
import { AssistantRuntimeProvider } from '@assistant-ui/react'
import {
  AssistantChatTransport,
  useChatRuntime
} from '@assistant-ui/react-ai-sdk'
import { ComfyApp } from '@comfyorg/comfyui-frontend-types'
import { type UIMessage, lastAssistantMessageIsCompleteWithToolCalls } from 'ai'
import { useEffect, useState } from 'react'

import {
  OnboardingView,
  fetchOnboardingStatus
} from '@/components/assistant-ui/onboarding'
import { Thread } from '@/components/assistant-ui/thread'
import { ProviderWizard } from '@/components/providers/ProviderWizard'
import {
  OPEN_PROVIDER_WIZARD_EVENT,
  type ProvidersStatus
} from '@/components/providers/types'
import { useComfyTools } from '@/hooks/useComfyTools'
import { useProviders } from '@/hooks/useProviders'

// Type definitions for the global ComfyUI objects
declare global {
  interface Window {
    app?: ComfyApp
  }
}

/**
 * Resubmit when the last assistant message has completed tool calls AND
 * the LLM hasn't responded to them yet.
 *
 * useChatRuntime appends the follow-up LLM response to the SAME message,
 * so after the LLM responds the parts look like:
 *   [text, tool-invocation(result), text]   ← last part is text → stop
 * vs right after tool execution:
 *   [text, tool-invocation(result)]          ← last part is tool → resubmit
 *
 * To prevent infinite loops, we limit auto-resubmit to 3 rounds maximum.
 */
const MAX_TOOL_ROUNDTRIPS = 3
let toolRoundtripCount = 0

function shouldResubmitAfterToolResult({
  messages
}: {
  messages: UIMessage[]
}): boolean {
  if (!lastAssistantMessageIsCompleteWithToolCalls({ messages })) {
    // Reset counter when no tool calls
    toolRoundtripCount = 0
    return false
  }

  const lastMsg = messages[messages.length - 1]
  const parts = lastMsg?.parts ?? []

  if (parts.length === 0) {
    toolRoundtripCount = 0
    return false
  }

  const lastPartType = parts[parts.length - 1].type
  const shouldResubmit = lastPartType !== 'text'

  if (shouldResubmit) {
    toolRoundtripCount++
    console.log(
      `[ComfyAssistant] Tool roundtrip ${toolRoundtripCount}/${MAX_TOOL_ROUNDTRIPS}`
    )

    if (toolRoundtripCount > MAX_TOOL_ROUNDTRIPS) {
      console.log(
        '[ComfyAssistant] Max tool roundtrips reached, stopping auto-resubmit'
      )
      toolRoundtripCount = 0
      return false
    }
  } else {
    // Reset counter when LLM responds with text
    toolRoundtripCount = 0
  }

  // If the last part is text, the LLM has already responded to the tool results
  return shouldResubmit
}

// Inner component that has access to runtime context
function ChatWithTools() {
  // Register ComfyUI tools into the runtime's ModelContext.
  // The runtime handles execution, result submission, and multi-step loops.
  useComfyTools()

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      <Thread />
    </div>
  )
}

function AppContent() {
  const runtime = useChatRuntime({
    transport: new AssistantChatTransport({
      api: '/api/chat'
    }),
    sendAutomaticallyWhen: shouldResubmitAfterToolResult
  })

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ChatWithTools />
    </AssistantRuntimeProvider>
  )
}

function App() {
  const { fetchStatus: fetchProvidersStatus } = useProviders()
  const [needsOnboarding, setNeedsOnboarding] = useState<boolean | null>(null)
  const [providersStatus, setProvidersStatus] =
    useState<ProvidersStatus | null>(null)
  const [showWizard, setShowWizard] = useState(false)

  useEffect(() => {
    let mounted = true

    fetchOnboardingStatus()
      .then(({ needsOnboarding: needs }) => {
        if (mounted) setNeedsOnboarding(needs)
      })
      .catch(() => {
        if (mounted) setNeedsOnboarding(false)
      })

    fetchProvidersStatus()
      .then((status) => {
        if (mounted) setProvidersStatus(status)
      })
      .catch(() => {
        if (mounted) {
          setProvidersStatus({
            needsWizard: false,
            hasProviders: true,
            activeProvider: null
          })
        }
      })

    const handleOpenProviderWizard = () => setShowWizard(true)
    window.addEventListener(
      OPEN_PROVIDER_WIZARD_EVENT,
      handleOpenProviderWizard as EventListener
    )

    return () => {
      mounted = false
      window.removeEventListener(
        OPEN_PROVIDER_WIZARD_EVENT,
        handleOpenProviderWizard as EventListener
      )
    }
  }, [fetchProvidersStatus])

  if (needsOnboarding === null || providersStatus === null) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        Loading…
      </div>
    )
  }

  if (providersStatus.needsWizard || showWizard) {
    return (
      <ProviderWizard
        mode="full-page"
        onComplete={() => {
          setShowWizard(false)
          setProvidersStatus({
            ...providersStatus,
            needsWizard: false,
            hasProviders: true
          })
        }}
      />
    )
  }

  if (needsOnboarding) {
    return <OnboardingView onComplete={() => setNeedsOnboarding(false)} />
  }

  return <AppContent />
}

export default App
