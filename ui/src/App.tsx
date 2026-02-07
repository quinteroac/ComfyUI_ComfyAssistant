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

import { ComfyApp } from '@comfyorg/comfyui-frontend-types'
import { AssistantRuntimeProvider } from "@assistant-ui/react"
import { useChatRuntime, AssistantChatTransport } from "@assistant-ui/react-ai-sdk"
import { lastAssistantMessageIsCompleteWithToolCalls } from "ai"
import { useEffect, useState } from "react"
import { ThreadList } from "@/components/assistant-ui/thread-list"
import { Thread } from "@/components/assistant-ui/thread"
import { OnboardingView, fetchOnboardingStatus } from "@/components/assistant-ui/onboarding"
import { useComfyTools } from "@/hooks/useComfyTools"
import './App.css'

// Type definitions for the global ComfyUI objects
declare global {
  interface Window {
    app?: ComfyApp
  }
}

// Inner component that has access to runtime context
function ChatWithTools() {
  // Register ComfyUI tools into the runtime's ModelContext.
  // The runtime handles execution, result submission, and multi-step loops.
  useComfyTools()

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      <ThreadList />
      <Thread />
    </div>
  )
}

function AppContent() {
  const runtime = useChatRuntime({
    transport: new AssistantChatTransport({
      api: "/api/chat",
    }),
    sendAutomaticallyWhen: lastAssistantMessageIsCompleteWithToolCalls,
  })

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ChatWithTools />
    </AssistantRuntimeProvider>
  )
}

function App() {
  const [needsOnboarding, setNeedsOnboarding] = useState<boolean | null>(null)

  useEffect(() => {
    fetchOnboardingStatus()
      .then(({ needsOnboarding: needs }) => setNeedsOnboarding(needs))
      .catch(() => setNeedsOnboarding(false))
  }, [])

  if (needsOnboarding === null) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        Loading…
      </div>
    )
  }

  if (needsOnboarding) {
    return (
      <OnboardingView
        onComplete={() => setNeedsOnboarding(false)}
      />
    )
  }

  return <AppContent />
}

export default App
