/**
 * Hook for slash command parsing, execution, and autocomplete.
 *
 * Intercepts user input starting with "/" and routes to registered commands.
 * Returns tryExecute (for submit handler) and getSuggestions (for autocomplete).
 */
import { useAssistantApi } from '@assistant-ui/react'

import {
  COMMANDS,
  type SlashCommand,
  type SlashCommandContext
} from '@/slash-commands'

export function useSlashCommands() {
  const api = useAssistantApi()
  const localPrefix = '<!-- local:slash -->\n'

  const appendLocal = (text: string) => {
    api.thread().append({
      role: 'assistant',
      content: [{ type: 'text', text: `${localPrefix}${text}` }],
      startRun: false
    })
  }

  const ctx: SlashCommandContext = {
    threadApi: api.thread() as SlashCommandContext['threadApi'],
    threadsApi: api.threads() as SlashCommandContext['threadsApi'],
    appendLocal
  }

  /**
   * Returns true if the input was handled as a command.
   * Call this before sending to the LLM.
   */
  const tryExecute = (input: string): boolean => {
    const trimmed = input.trim()
    if (!trimmed.startsWith('/')) return false

    const spaceIdx = trimmed.indexOf(' ')
    const name = (
      spaceIdx === -1 ? trimmed.slice(1) : trimmed.slice(1, spaceIdx)
    ).toLowerCase()
    const args = spaceIdx === -1 ? '' : trimmed.slice(spaceIdx + 1).trim()

    // Backend-managed commands: send to backend as-is.
    if (name === 'skill' || name === 'provider') {
      return false
    }

    const cmd = COMMANDS.find((c) => c.name === name)
    if (!cmd) {
      appendLocal(
        `Unknown command: /${name}. Type /help for available commands.`
      )
      return true
    }

    cmd.execute(args, ctx)
    return true
  }

  /**
   * Returns matching commands for autocomplete when user types "/".
   */
  const getSuggestions = (input: string): SlashCommand[] => {
    if (!input.startsWith('/')) return []
    const partial = input.slice(1).toLowerCase()
    if (!partial) return COMMANDS
    return COMMANDS.filter((c) => c.name.startsWith(partial))
  }

  return { tryExecute, getSuggestions }
}
