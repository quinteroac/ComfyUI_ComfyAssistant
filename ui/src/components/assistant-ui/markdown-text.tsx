'use client'

import { useMessage } from '@assistant-ui/react'
import {
  type CodeHeaderProps,
  unstable_memoizeMarkdownComponents as memoizeMarkdownComponents,
  useIsMarkdownCodeBlock
} from '@assistant-ui/react-markdown'
import '@assistant-ui/react-markdown/styles/dot.css'
import { CheckIcon, CopyIcon } from 'lucide-react'
import { type FC, memo, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkBreaks from 'remark-breaks'
import remarkGfm from 'remark-gfm'

import { TooltipIconButton } from '@/components/assistant-ui/tooltip-icon-button'
import { cn } from '@/lib/utils'

const MarkdownTextImpl = () => {
  const message = useMessage()
  const textParts = message.content.filter((p) => p.type === 'text')
  const texts = textParts.map((p) => (p as { text: string }).text).filter(Boolean)
  const seen = new Set<string>()
  const deduped = texts.filter((t) => {
    if (seen.has(t)) return false
    seen.add(t)
    return true
  })
  const fullText = deduped.length > 0 ? deduped.join('\n\n') : ''
  const cleanedText = fullText.replace(/^<!-- local:slash -->\n?/, '')

  if (!cleanedText) return null
  return (
    <div className="aui-md text-[15px]">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkBreaks]}
        components={defaultComponents as any}
      >
        {cleanedText}
      </ReactMarkdown>
    </div>
  )
}

export const MarkdownText = memo(MarkdownTextImpl)

const CodeHeader: FC<CodeHeaderProps> = ({ language, code }) => {
  const { isCopied, copyToClipboard } = useCopyToClipboard()
  const onCopy = () => {
    if (!code || isCopied) return
    copyToClipboard(code)
  }

  return (
    <div className="aui-code-header-root mt-1 flex items-center justify-between rounded-t border border-border/50 border-b-0 bg-muted/50 px-2 py-0.5 text-[10px]">
      <span className="aui-code-header-language font-medium text-muted-foreground lowercase">
        {language}
      </span>
      <TooltipIconButton tooltip="Copy" onClick={onCopy}>
        {!isCopied && <CopyIcon />}
        {isCopied && <CheckIcon />}
      </TooltipIconButton>
    </div>
  )
}

const useCopyToClipboard = ({
  copiedDuration = 3000
}: {
  copiedDuration?: number
} = {}) => {
  const [isCopied, setIsCopied] = useState<boolean>(false)

  const copyToClipboard = (value: string) => {
    if (!value) return

    navigator.clipboard
      .writeText(value)
      .then(() => {
        setIsCopied(true)
        setTimeout(() => setIsCopied(false), copiedDuration)
      })
      .catch(console.error)
  }

  return { isCopied, copyToClipboard }
}

const defaultComponents = memoizeMarkdownComponents({
  h1: ({ className, ...props }) => (
    <h1
      className={cn(
        'aui-md-h1 mb-1 scroll-m-20 font-semibold text-sm first:mt-0 last:mb-0',
        className
      )}
      {...props}
    />
  ),
  h2: ({ className, ...props }) => (
    <h2
      className={cn(
        'aui-md-h2 mt-2 mb-1 scroll-m-20 font-semibold text-sm first:mt-0 last:mb-0',
        className
      )}
      {...props}
    />
  ),
  h3: ({ className, ...props }) => (
    <h3
      className={cn(
        'aui-md-h3 mt-1.5 mb-0.5 scroll-m-20 font-semibold text-[13px] first:mt-0 last:mb-0',
        className
      )}
      {...props}
    />
  ),
  h4: ({ className, ...props }) => (
    <h4
      className={cn(
        'aui-md-h4 mt-1 mb-0.5 scroll-m-20 font-medium text-[13px] first:mt-0 last:mb-0',
        className
      )}
      {...props}
    />
  ),
  h5: ({ className, ...props }) => (
    <h5
      className={cn(
        'aui-md-h5 mt-1 mb-0.5 font-medium text-[13px] first:mt-0 last:mb-0',
        className
      )}
      {...props}
    />
  ),
  h6: ({ className, ...props }) => (
    <h6
      className={cn(
        'aui-md-h6 mt-1 mb-0.5 font-medium text-[13px] first:mt-0 last:mb-0',
        className
      )}
      {...props}
    />
  ),
  p: ({ className, ...props }) => (
    <p
      className={cn(
        'aui-md-p my-1 leading-normal first:mt-0 last:mb-0',
        className
      )}
      {...props}
    />
  ),
  a: ({ className, ...props }) => (
    <a
      className={cn(
        'aui-md-a text-primary underline underline-offset-2 hover:text-primary/80',
        className
      )}
      {...props}
    />
  ),
  blockquote: ({ className, ...props }) => (
    <blockquote
      className={cn(
        'aui-md-blockquote my-1 border-muted-foreground/30 border-l-2 pl-2 text-muted-foreground italic',
        className
      )}
      {...props}
    />
  ),
  ul: ({ className, ...props }) => (
    <ul
      className={cn(
        'aui-md-ul my-1 ml-3 list-disc marker:text-muted-foreground [&>li]:mt-0.5',
        className
      )}
      {...props}
    />
  ),
  ol: ({ className, ...props }) => (
    <ol
      className={cn(
        'aui-md-ol my-1 ml-3 list-decimal marker:text-muted-foreground [&>li]:mt-0.5',
        className
      )}
      {...props}
    />
  ),
  hr: ({ className, ...props }) => (
    <hr
      className={cn('aui-md-hr my-1 border-muted-foreground/20', className)}
      {...props}
    />
  ),
  table: ({ className, ...props }) => (
    <table
      className={cn(
        'aui-md-table my-1 w-full border-separate border-spacing-0 overflow-y-auto text-xs',
        className
      )}
      {...props}
    />
  ),
  th: ({ className, ...props }) => (
    <th
      className={cn(
        'aui-md-th bg-muted px-1.5 py-0.5 text-left font-medium first:rounded-tl last:rounded-tr [[align=center]]:text-center [[align=right]]:text-right',
        className
      )}
      {...props}
    />
  ),
  td: ({ className, ...props }) => (
    <td
      className={cn(
        'aui-md-td border-muted-foreground/20 border-b border-l px-1.5 py-0.5 text-left last:border-r [[align=center]]:text-center [[align=right]]:text-right',
        className
      )}
      {...props}
    />
  ),
  tr: ({ className, ...props }) => (
    <tr
      className={cn(
        'aui-md-tr m-0 border-b p-0 first:border-t [&:last-child>td:first-child]:rounded-bl [&:last-child>td:last-child]:rounded-br',
        className
      )}
      {...props}
    />
  ),
  li: ({ className, ...props }) => (
    <li className={cn('aui-md-li leading-normal', className)} {...props} />
  ),
  sup: ({ className, ...props }) => (
    <sup
      className={cn('aui-md-sup [&>a]:text-xs [&>a]:no-underline', className)}
      {...props}
    />
  ),
  pre: ({ className, ...props }) => (
    <pre
      className={cn(
        'aui-md-pre overflow-x-auto rounded-t-none rounded-b border border-border/50 border-t-0 bg-muted/30 p-2 text-xs leading-relaxed',
        className
      )}
      {...props}
    />
  ),
  code: function Code({ className, ...props }) {
    const isCodeBlock = useIsMarkdownCodeBlock()
    return (
      <code
        className={cn(
          !isCodeBlock &&
            'aui-md-inline-code rounded border border-border/50 bg-muted/50 px-1 py-0.5 text-[0.9em]',
          className
        )}
        {...props}
      />
    )
  },
  CodeHeader
})
