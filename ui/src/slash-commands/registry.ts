/**
 * Slash command registry for terminal-style assistant UI.
 *
 * Commands are invoked by typing "/" followed by the command name (e.g. /help).
 * Each command has an execute function that receives parsed args and context.
 */
import type { SlashCommandContext } from './types'

export interface SlashCommand {
  name: string
  description: string
  usage: string
  execute: (args: string, ctx: SlashCommandContext) => void
}

export type { SlashCommandContext } from './types'
