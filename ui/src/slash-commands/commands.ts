/**
 * Slash command implementations.
 */
import type { SlashCommand } from './registry'
import type { SlashCommandContext } from './types'

const LOCAL_PREFIX = '<!-- local:slash -->'
const DEFAULT_COMPACT_KEEP = 6
const MAX_COMPACT_KEEP = 30

function extractText(message: unknown): string {
  if (!message || typeof message !== 'object') return ''
  const msg = message as {
    content?: unknown
    parts?: Array<{ type?: string; text?: string }>
  }

  if (typeof msg.content === 'string') return msg.content
  if (Array.isArray(msg.content)) {
    const chunks = msg.content
      .map((part) => {
        if (!part || typeof part !== 'object') return ''
        const p = part as { type?: string; text?: string }
        return p.type === 'text' && typeof p.text === 'string' ? p.text : ''
      })
      .filter(Boolean)
    if (chunks.length > 0) return chunks.join('')
  }
  if (Array.isArray(msg.parts)) {
    return msg.parts
      .map((p) => (p.type === 'text' && p.text ? p.text : ''))
      .filter(Boolean)
      .join('')
  }
  return ''
}

function isLocalSlashMessage(message: unknown): boolean {
  return extractText(message).includes(LOCAL_PREFIX)
}

function makeLocalMessage(text: string): unknown {
  return {
    role: 'assistant',
    content: [{ type: 'text', text: `${LOCAL_PREFIX}\n${text}` }],
    startRun: false
  }
}

function cmdHelp(_args: string, ctx: SlashCommandContext) {
  const lines = [
    '**Available commands**',
    '',
    '| Command | Description |',
    '|---------|-------------|',
    '| `/help` | Show this help message |',
    '| `/skill <name>` | Activate a user skill by name or slug (e.g. `/skill use-preview-image`) |',
    '| `/clear` | Reset current thread to initial empty state |',
    '| `/compact [keep]` | Compact context and keep recent messages |',
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
  ctx.threadApi.reset([])
}

function cmdCompact(args: string, ctx: SlashCommandContext) {
  const requested = Number(args.trim())
  const keep = Number.isInteger(requested)
    ? Math.min(Math.max(requested, 1), MAX_COMPACT_KEEP)
    : DEFAULT_COMPACT_KEEP

  const state = ctx.threadApi.getState()
  const allMessages = Array.isArray(state.messages) ? [...state.messages] : []
  const nonLocalMessages = allMessages.filter((m) => !isLocalSlashMessage(m))
  if (nonLocalMessages.length === 0) {
    ctx.appendLocal('Nothing to compact in this session yet.')
    return
  }

  const preserved = nonLocalMessages.slice(-keep)
  const removed = nonLocalMessages.length - preserved.length
  if (removed <= 0) {
    ctx.appendLocal(
      `Context is already compact. Kept ${preserved.length} message(s).`
    )
    return
  }

  const summary = [
    '**Context compacted**',
    '',
    `Removed ${removed} older message(s).`,
    `Kept ${preserved.length} most recent message(s).`,
    '',
    'Use `/compact <n>` to keep a different number of recent messages.'
  ].join('\n')

  ctx.threadApi.reset([makeLocalMessage(summary), ...preserved])
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
    name: 'skill',
    description: 'Activate a user skill by name or slug',
    usage: '/skill <name>',
    execute: () => {} // Handled by backend; message is sent as-is
  },
  {
    name: 'clear',
    description: 'Clear messages in current thread',
    usage: '/clear',
    execute: cmdClear
  },
  {
    name: 'compact',
    description: 'Compact context and keep recent messages',
    usage: '/compact [keep]',
    execute: cmdCompact
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
