'use client'

import {
  MessagePrimitive,
  useAuiState,
  useMessage
} from '@assistant-ui/react'
import { memo, useMemo } from 'react'

import { stripLocalMessageComments } from '@/lib/utils'
import { MarkdownBlock } from '@/components/assistant-ui/markdown-text'
import { ToolFallback } from '@/components/assistant-ui/tool-fallback'

type ContentPart = { type: string; text?: string; [key: string]: unknown }

type Block =
  | { type: 'text'; text: string; startIndex: number }
  | { type: 'tool-call'; index: number }
  | { type: 'reasoning'; index: number }
  | { type: 'other'; index: number }

/**
 * Build ordered blocks from message.content:
 * - Consecutive text parts → single block (merged, deduped within group)
 * - tool-call, reasoning, etc. → one block each
 */
function buildBlocks(content: ContentPart[]): Block[] {
  const blocks: Block[] = []
  let textBuffer: string[] = []
  const seenInGroup = new Set<string>()

  const flushTextBlock = (startIndex: number) => {
    if (textBuffer.length === 0) return
    const merged = textBuffer.join('\n\n')
    textBuffer = []
    seenInGroup.clear()
    blocks.push({ type: 'text', text: merged, startIndex })
  }

  for (let i = 0; i < content.length; i++) {
    const part = content[i]
    if (!part) continue

    if (part.type === 'text') {
      const raw = (part.text as string) ?? ''
      const t = raw.trim()
      if (!t) continue
      if (seenInGroup.has(t)) continue
      seenInGroup.add(t)
      textBuffer.push(raw)
      continue
    }

    flushTextBlock(i)
    if (part.type === 'tool-call') {
      blocks.push({ type: 'tool-call', index: i })
    } else if (part.type === 'reasoning') {
      blocks.push({ type: 'reasoning', index: i })
    } else {
      blocks.push({ type: 'other', index: i })
    }
  }

  flushTextBlock(content.length)
  return blocks
}

const InterleavedMessageContentImpl = () => {
  const message = useMessage()
  // AI SDK uses `parts`, assistant-ui thread uses `content` — support both
  const msg = message as unknown as { parts?: ContentPart[]; content?: ContentPart[] }
  const rawContent = msg.parts ?? msg.content ?? []
  const content = Array.isArray(rawContent) ? rawContent : []

  const partsLength = useAuiState(
    (s) => (Array.isArray(s.message?.parts) ? s.message.parts.length : 0)
  )

  const blocks = useMemo(() => buildBlocks(content), [content])

  if (blocks.length === 0) return null

  return (
    <>
      {blocks.map((block, blockIdx) => {
        if (block.type === 'text') {
          const cleaned = stripLocalMessageComments(block.text)
          if (!cleaned.trim()) return null
          return (
            <MarkdownBlock key={`text-${block.startIndex}-${blockIdx}`}>
              {cleaned}
            </MarkdownBlock>
          )
        }

        if (block.type === 'tool-call') {
          if (block.index >= partsLength) return null
          return (
            <MessagePrimitive.PartByIndex
              key={`tool-${block.index}`}
              index={block.index}
              components={{
                Text: () => null,
                Reasoning: () => null,
                tools: { Fallback: ToolFallback }
              }}
            />
          )
        }

        if (block.type === 'reasoning') {
          if (block.index >= partsLength) return null
          return (
            <MessagePrimitive.PartByIndex
              key={`reasoning-${block.index}`}
              index={block.index}
              components={{
                Text: () => null,
                Reasoning: (props) => (
                  <details
                    className="aui-reasoning-root"
                    data-part="reasoning"
                  >
                    <summary className="aui-reasoning-header">
                      Chain of Thought
                    </summary>
                    <div className="aui-reasoning-content">{props.text}</div>
                  </details>
                ),
                tools: { Fallback: ToolFallback }
              }}
            />
          )
        }

        return null
      })}
    </>
  )
}

export const InterleavedMessageContent = memo(InterleavedMessageContentImpl)
