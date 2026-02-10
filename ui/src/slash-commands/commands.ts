/**
 * Slash command implementations: /help, /clear, /new, /rename, /sessions.
 */
import type { SlashCommand } from './registry'
import type { SlashCommandContext } from './types'

function cmdHelp(_args: string, ctx: SlashCommandContext) {
  const lines = [
    '**Available commands**',
    '',
    '| Command | Description |',
    '|---------|-------------|',
    '| `/help` | Show this help message |',
    '| `/clear` | Clear all messages in the current thread |',
    '| `/new` | Create and switch to a new session |',
    '| `/rename <name>` | Rename the current session |',
    '| `/session <id>` | Switch to a session by id |',
    '| `/sessions` | List all sessions |',
    '',
    'Type a message to chat with the assistant. Use slash commands for quick actions.'
  ]
  ctx.appendLocal(lines.join('\n'))
}

function cmdClear(_args: string, ctx: SlashCommandContext) {
  ctx.threadApi.reset()
}

function cmdNew(_args: string, ctx: SlashCommandContext) {
  ctx.threadsApi.switchToNewThread()
}

function cmdRename(args: string, ctx: SlashCommandContext) {
  const name = args.trim()
  if (!name) {
    ctx.appendLocal('Usage: /rename <name>\nExample: /rename my-workflow')
    return
  }
  const { mainThreadId } = ctx.threadsApi.getState()
  ctx.threadsApi.item({ id: mainThreadId }).rename(name)
  ctx.appendLocal(`Session renamed to "${name}"`)
}

function cmdSessions(_args: string, ctx: SlashCommandContext) {
  const { mainThreadId, threadIds } = ctx.threadsApi.getState()
  if (threadIds.length === 0) {
    ctx.appendLocal(
      'No sessions yet. Type a message or use /new to create one.'
    )
    return
  }
  const lines = ['**Sessions**', '']
  threadIds.forEach((id, index) => {
    const item = ctx.threadsApi.item({ id })
    const state = item.getState()
    const title = state.title || 'New Chat'
    const marker = id === mainThreadId ? ' **(current)**' : ''
    lines.push(`${index + 1}. ${title} \`(${id})\`${marker}`)
  })
  ctx.appendLocal(lines.join('\n'))
}

function cmdSession(args: string, ctx: SlashCommandContext) {
  const token = args.trim()
  if (!token) {
    ctx.appendLocal(
      'Usage: /session <id|index|name>\nExamples: /session 2, /session __LOCALID_xxx, /session my-workflow'
    )
    return
  }

  const { threadIds } = ctx.threadsApi.getState()

  // 1) Numeric index (1-based, as printed by /sessions)
  const index = Number(token)
  if (Number.isInteger(index) && index >= 1 && index <= threadIds.length) {
    const targetId = threadIds[index - 1]
    ctx.threadsApi.switchToThread(targetId)
    ctx.appendLocal(`Switched to session ${index}`)
    return
  }

  // 2) Exact ID match
  if (threadIds.includes(token)) {
    ctx.threadsApi.switchToThread(token)
    ctx.appendLocal(`Switched to session ${token}`)
    return
  }

  // 3) Title match (case-insensitive)
  const matchId = threadIds.find((id) => {
    const item = ctx.threadsApi.item({ id })
    const state = item.getState()
    const title = (state.title || 'New Chat').toLowerCase()
    return title === token.toLowerCase()
  })

  if (!matchId) {
    ctx.appendLocal(`Session not found: ${token}`)
    return
  }

  ctx.threadsApi.switchToThread(matchId)
  ctx.appendLocal(`Switched to session ${token}`)
}

export const COMMANDS: SlashCommand[] = [
  {
    name: 'help',
    description: 'Show available commands',
    usage: '/help',
    execute: cmdHelp
  },
  {
    name: 'clear',
    description: 'Clear messages in current thread',
    usage: '/clear',
    execute: cmdClear
  },
  {
    name: 'new',
    description: 'Create new session',
    usage: '/new',
    execute: cmdNew
  },
  {
    name: 'rename',
    description: 'Rename current session',
    usage: '/rename <name>',
    execute: cmdRename
  },
  {
    name: 'session',
    description: 'Switch to a session by id, index, or name',
    usage: '/session <id|index|name>',
    execute: cmdSession
  },
  {
    name: 'sessions',
    description: 'List all sessions',
    usage: '/sessions',
    execute: cmdSessions
  }
]
