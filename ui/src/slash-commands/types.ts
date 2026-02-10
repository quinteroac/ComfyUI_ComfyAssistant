/**
 * Context passed to slash command handlers.
 * Provides access to thread, threads, and a helper to append local-only messages.
 */
export interface SlashCommandContext {
  threadApi: {
    reset: (initialMessages?: readonly unknown[]) => void
    append: (message: unknown) => void
    composer: {
      getState: () => { text: string }
      setText: (t: string) => void
      send: () => void
    }
  }
  threadsApi: {
    getState: () => { mainThreadId: string; threadIds: readonly string[] }
    switchToThread: (threadId: string) => void
    switchToNewThread: () => void
    item: (opts: { id: string }) => {
      rename: (title: string) => void
      getState: () => { id: string; title?: string }
    }
  }
  appendLocal: (text: string) => void
}
