import {
  ActionBarMorePrimitive,
  ActionBarPrimitive,
  AuiIf,
  BranchPickerPrimitive,
  ComposerPrimitive,
  ErrorPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useAssistantApi,
  useAssistantState
} from '@assistant-ui/react'
import {
  ArrowDownIcon,
  ArrowUpIcon,
  CheckIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CopyIcon,
  DownloadIcon,
  MoreHorizontalIcon,
  PencilIcon,
  RefreshCwIcon,
  SquareIcon
} from 'lucide-react'
import { createPortal } from 'react-dom'
import { useCallback, useLayoutEffect, useMemo, useRef, useState } from 'react'
import type { FC, KeyboardEvent, RefObject } from 'react'

import {
  ComposerAddAttachment,
  ComposerAttachments,
  UserMessageAttachments
} from '@/components/assistant-ui/attachment'
import { MarkdownText } from '@/components/assistant-ui/markdown-text'
import { ToolFallback } from '@/components/assistant-ui/tool-fallback'
import { TooltipIconButton } from '@/components/assistant-ui/tooltip-icon-button'
import { Button } from '@/components/ui/button'
import { useSlashCommands } from '@/hooks/useSlashCommands'
import { cn } from '@/lib/utils'

import './terminal-theme.css'

const ASCII_LOGO = `▛▛▛▛▛▛▛▛▛▛▛▛▛▛▛▛▛▛▛▛▛▛▛▛▛▛▛▛▛█
▛█▜▛█▜▛█▜▛█▜▛█▜▛█▜▛█▜▛█▜▛█▜▛█▜
▛▛█▟▜▙▛▛▙▛▛▙▛▛▙▛▛▙▛▛▙▛▛▙▛▛▙▛▛█
▛█▚▛█▟▜▛▛▛█▜▜▜▘▀▝▝▝▘▘▘▀▘█▜▜▜▛█
▛▛▛▛▙▛▙▛█▜▙█▜▘  ▖▗  ▖  ▝▛█▜▜▟█
▛█▜▛▙▛▙█▜▙▜▞▛  ▘   ▘ ▝ ▛▛▙█▜▙█
▛▛▙█▙█▜▟▘    ▗ ▖▗▝  ▖▗▐▜▛█▟▜▟▜
▛█▜▟▟▟▜▞ ▖▗ ▘ ▟▜▙▛█▛█▜▜▜▟▙▛█▟█
▛▛█▞▙▛▛▌    ▖▗▛█▟▜▙▛▙█▜▛▙▙▛▙▙█
▛▛▙▛▙█▀  ▘▝  ▟▜▙▜▙▙█▜▟▜▜▙▛▛▙█▟
▛█▙█▜▟▘▖▘ ▖ ▘▛█▟▜▟▚▛█▟▛█▞▛█▙▙█
▛▙▙▛█▟   ▖ ▖        ▙▙▛▙█▜▙▙▛▟
▛▙█▟▙▛██▜▖  ▝ ▖ ▖▗▝▗▜▟▜▙▛█▟▟▜█
▛█▟▟▟▜▙▜▜  ▘▗  ▖   ▟▜▟█▟▜▟▟▟▜▟
▛▙▙▛▟▜▟▜▙▄▄▄▄▖▌▄▄▚▟▟▛▙▙▜▜▟▙▛▛█
▛▙▛▛█▜▟█▟▙█▟▟▜▜▙▜▜▟▙▛▙▛█▜▟▟▜▜█
▛▛▛▛▙█▚▙▙▙▙▛▟▛█▟▜█▟▟▜▙▛▛▛▙▛▛█▟
█████▟█▙█▟▙█▙█▙██▟▟▟█▟███▙██▙█`

export const Thread: FC = () => {
  return (
    <ThreadPrimitive.Root className="aui-root aui-thread-root @container flex h-full min-h-0 flex-col bg-background">
      <ThreadPrimitive.Viewport className="aui-thread-viewport relative flex min-h-0 flex-1 flex-col overflow-x-auto overflow-y-auto scroll-smooth px-3 pt-2">
        <AuiIf condition={({ thread }) => thread.isEmpty}>
          <ThreadWelcome />
        </AuiIf>

        <ThreadPrimitive.Messages
          components={{
            UserMessage,
            EditComposer,
            AssistantMessage
          }}
        />

        <ThreadPrimitive.ViewportFooter className="aui-thread-viewport-footer sticky bottom-0 mt-auto flex w-full flex-col gap-2 overflow-visible pb-2">
          <ThreadScrollToBottom />
        </ThreadPrimitive.ViewportFooter>
      </ThreadPrimitive.Viewport>

      <div className="aui-composer-outer flex-shrink-0 px-3 pb-2">
        <Composer />
      </div>
    </ThreadPrimitive.Root>
  )
}

const ThreadScrollToBottom: FC = () => {
  return (
    <ThreadPrimitive.ScrollToBottom asChild>
      <TooltipIconButton
        tooltip="Scroll to bottom"
        variant="outline"
        className="aui-thread-scroll-to-bottom absolute -top-8 z-10 self-center rounded p-2 disabled:invisible dark:bg-background dark:hover:bg-accent"
      >
        <ArrowDownIcon />
      </TooltipIconButton>
    </ThreadPrimitive.ScrollToBottom>
  )
}

const ThreadWelcome: FC = () => {
  return (
    <div className="aui-thread-welcome-root my-auto flex w-full grow flex-col items-start justify-center">
      <pre className="text-muted-foreground text-[13px] leading-tight select-none opacity-60">
        {ASCII_LOGO}
      </pre>
      <p className="aui-thread-welcome-message-inner mt-2 text-muted-foreground text-[13px]">
        Type a message or /help to get started
      </p>
    </div>
  )
}

const Composer: FC = () => {
  const api = useAssistantApi()
  const { tryExecute, getSuggestions } = useSlashCommands()
  const composerText = useAssistantState((s) => s.composer.text)
  const [selectedIndex, setSelectedIndex] = useState(0)
  const dropzoneRef = useRef<HTMLDivElement>(null)
  const suggestions = getSuggestions(composerText)
  const showAutocomplete =
    composerText.startsWith('/') && suggestions.length > 0

  const handleSubmit = useCallback(() => {
    const text = api.thread().composer.getState().text
    if (!text.trim()) return
    if (tryExecute(text)) {
      api.thread().composer.setText('')
    } else {
      api.thread().composer.send()
    }
  }, [api, tryExecute])

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (showAutocomplete) {
        if (e.key === 'ArrowDown') {
          e.preventDefault()
          setSelectedIndex((i) => Math.min(i + 1, suggestions.length - 1))
          return
        }
        if (e.key === 'ArrowUp') {
          e.preventDefault()
          setSelectedIndex((i) => Math.max(i - 1, 0))
          return
        }
        if (e.key === 'Enter' || e.key === 'Tab') {
          const cmd = suggestions[selectedIndex]
          if (cmd) {
            e.preventDefault()
            api.thread().composer.setText(`/${cmd.name} `)
            setSelectedIndex(0)
            return
          }
        }
        if (e.key === 'Escape') {
          setSelectedIndex(0)
        }
      }
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSubmit()
      }
    },
    [showAutocomplete, suggestions, selectedIndex, api, handleSubmit]
  )

  const handleSuggestionClick = useCallback(
    (cmd: { name: string }) => {
      api.thread().composer.setText(`/${cmd.name} `)
      setSelectedIndex(0)
    },
    [api]
  )

  return (
    <ComposerPrimitive.Root className="aui-composer-root relative flex w-full items-center gap-1">
        <span
          className="shrink-0 select-none text-[15px] font-medium"
          style={{ color: 'hsl(var(--terminal-prompt))' }}
        >
          ›
        </span>
      <ComposerPrimitive.AttachmentDropzone
        ref={dropzoneRef}
        className="aui-composer-attachment-dropzone relative flex w-full flex-col rounded border border-border bg-transparent outline-none transition-colors has-[textarea:focus-visible]:border-ring data-[dragging=true]:border-ring data-[dragging=true]:border-dashed"
      >
        <ComposerAttachments />
        {showAutocomplete && (
          <SlashCommandAutocomplete
            anchorRef={dropzoneRef}
            suggestions={suggestions}
            selectedIndex={selectedIndex}
            onSelect={handleSuggestionClick}
          />
        )}
        <ComposerPrimitive.Input asChild submitOnEnter={false}>
          <textarea
            placeholder="Send a message..."
            rows={1}
            onKeyDown={handleKeyDown}
            style={{
              height: 'auto',
              minHeight: '1.75rem',
              maxHeight: '4.5rem',
              resize: 'none',
              border: 'none',
              outline: 'none'
            }}
            className="aui-composer-input m-0 w-full overflow-y-auto border-0 bg-transparent px-2 py-1 text-[15px] outline-none placeholder:text-muted-foreground focus-visible:ring-0 focus:border-0 focus:outline-none"
            aria-label="Message input"
          />
        </ComposerPrimitive.Input>
        <ComposerAction onSubmit={handleSubmit} />
      </ComposerPrimitive.AttachmentDropzone>
    </ComposerPrimitive.Root>
  )
}

const SlashCommandAutocomplete: FC<{
  anchorRef: RefObject<HTMLElement>
  suggestions: Array<{ name: string; description: string }>
  selectedIndex: number
  onSelect: (cmd: { name: string }) => void
}> = ({ anchorRef, suggestions, selectedIndex, onSelect }) => {
  const [style, setStyle] = useState<React.CSSProperties | null>(null)

  const portalRoot = useMemo(() => {
    return document.getElementById('comfyui-assistant-root') ?? document.body
  }, [])

  useLayoutEffect(() => {
    const anchor = anchorRef.current
    if (!anchor) return

    const updatePosition = () => {
      const rect = anchor.getBoundingClientRect()
      setStyle({
        position: 'fixed',
        left: rect.left,
        width: rect.width,
        bottom: window.innerHeight - rect.top + 8
      })
    }

    updatePosition()

    const resizeObserver = new ResizeObserver(updatePosition)
    resizeObserver.observe(anchor)
    window.addEventListener('resize', updatePosition)

    return () => {
      resizeObserver.disconnect()
      window.removeEventListener('resize', updatePosition)
    }
  }, [anchorRef])

  if (!style) return null

  return createPortal(
    <div
      className="aui-slash-autocomplete z-50 max-h-40 overflow-y-auto rounded border px-0.5 py-1"
      style={style}
    >
      <ul className="list-none p-0 m-0">
        {suggestions.map((cmd, i) => (
          <li key={cmd.name}>
            <button
              type="button"
              className={cn(
                'aui-slash-cmd-item flex w-full cursor-pointer items-center justify-between rounded px-2 py-1 text-left text-xs outline-none',
                i === selectedIndex && 'bg-accent'
              )}
              onClick={() => onSelect(cmd)}
              onMouseDown={(e) => e.preventDefault()}
            >
              <span className="aui-slash-cmd-name font-medium">/{cmd.name}</span>
              <span className="aui-slash-cmd-desc ml-2 max-w-[160px] truncate">
                {cmd.description}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>,
    portalRoot
  )
}

const ComposerAction: FC<{ onSubmit: () => void }> = ({ onSubmit }) => {
  const isEmpty = useAssistantState((s) => s.composer.isEmpty)

  return (
    <div className="aui-composer-action-wrapper absolute right-1 bottom-0.5 flex items-center gap-0.5">
      <ComposerAddAttachment />
      <AuiIf condition={({ thread }) => !thread.isRunning}>
        <TooltipIconButton
          tooltip="Send"
          side="top"
          type="button"
          variant="default"
          size="icon"
          className="aui-composer-send size-6 rounded disabled:opacity-50"
          aria-label="Send message"
          disabled={isEmpty}
          onClick={onSubmit}
        >
          <ArrowUpIcon className="aui-composer-send-icon size-3.5" />
        </TooltipIconButton>
      </AuiIf>
      <AuiIf condition={({ thread }) => thread.isRunning}>
        <ComposerPrimitive.Cancel asChild>
          <Button
            type="button"
            variant="default"
            size="icon"
            className="aui-composer-cancel size-6 rounded"
            aria-label="Stop generating"
          >
            <SquareIcon className="aui-composer-cancel-icon size-2.5 fill-current" />
          </Button>
        </ComposerPrimitive.Cancel>
      </AuiIf>
    </div>
  )
}

const MessageError: FC = () => {
  return (
    <MessagePrimitive.Error>
      <ErrorPrimitive.Root className="aui-message-error-root mt-1 rounded border border-destructive bg-destructive/10 p-1.5 text-destructive text-xs dark:bg-destructive/5 dark:text-red-200">
        <ErrorPrimitive.Message className="aui-message-error-message line-clamp-2" />
      </ErrorPrimitive.Root>
    </MessagePrimitive.Error>
  )
}

/* Prompt column width: matches "› " for alignment */
const PROMPT_WIDTH = '2ch'

const AssistantMessage: FC = () => {
  return (
    <MessagePrimitive.Root
      className="aui-assistant-message-root relative w-full py-0.5"
      data-role="assistant"
    >
      <div className="aui-assistant-message-row flex items-baseline gap-1">
        <span
          className="aui-assistant-prefix shrink-0 select-none text-[15px] leading-[1.5]"
          style={{ color: 'hsl(var(--terminal-dim))' }}
        >
          •
        </span>
        <div className="aui-assistant-message-content min-w-0 break-words text-[15px] text-foreground leading-relaxed">
          <MarkdownText />

          <MessagePrimitive.Parts
            components={{
              Text: () => null,
              Reasoning: (props) => (
                <details className="aui-reasoning-root" data-part="reasoning">
                  <summary className="aui-reasoning-header">
                    Chain of Thought
                  </summary>
                  <div className="aui-reasoning-content">{props.text}</div>
                </details>
              ),
              tools: { Fallback: ToolFallback }
            }}
          />
          <MessageError />
        </div>
      </div>

      <div
        className="aui-assistant-message-footer mt-0.5 flex"
        style={{ marginLeft: PROMPT_WIDTH }}
      >
        <BranchPicker />
        <AssistantActionBar />
      </div>
    </MessagePrimitive.Root>
  )
}

const AssistantActionBar: FC = () => {
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      autohideFloat="single-branch"
      className="aui-assistant-action-bar-root -ml-0.5 flex gap-0.5 text-muted-foreground data-floating:absolute data-floating:rounded data-floating:border data-floating:bg-background data-floating:p-0.5 data-floating:shadow-sm"
    >
      <ActionBarPrimitive.Copy asChild>
        <TooltipIconButton tooltip="Copy">
          <AuiIf condition={({ message }) => message.isCopied}>
            <CheckIcon />
          </AuiIf>
          <AuiIf condition={({ message }) => !message.isCopied}>
            <CopyIcon />
          </AuiIf>
        </TooltipIconButton>
      </ActionBarPrimitive.Copy>
      <ActionBarPrimitive.Reload asChild>
        <TooltipIconButton tooltip="Refresh">
          <RefreshCwIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.Reload>
      <ActionBarMorePrimitive.Root>
        <ActionBarMorePrimitive.Trigger asChild>
          <TooltipIconButton
            tooltip="More"
            className="data-[state=open]:bg-accent"
          >
            <MoreHorizontalIcon />
          </TooltipIconButton>
        </ActionBarMorePrimitive.Trigger>
        <ActionBarMorePrimitive.Content
          side="bottom"
          align="start"
          className="aui-action-bar-more-content z-50 min-w-28 overflow-hidden rounded border bg-popover p-0.5 text-popover-foreground shadow-md"
        >
          <ActionBarPrimitive.ExportMarkdown asChild>
            <ActionBarMorePrimitive.Item className="aui-action-bar-more-item flex cursor-pointer select-none items-center gap-1.5 rounded-sm px-2 py-1 text-xs outline-none hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground">
              <DownloadIcon className="size-3" />
              Export as Markdown
            </ActionBarMorePrimitive.Item>
          </ActionBarPrimitive.ExportMarkdown>
        </ActionBarMorePrimitive.Content>
      </ActionBarMorePrimitive.Root>
    </ActionBarPrimitive.Root>
  )
}

const UserMessage: FC = () => {
  return (
    <MessagePrimitive.Root
      className="aui-user-message-root relative w-full py-0.5"
      data-role="user"
    >
      <UserMessageAttachments />

      <div
        className="aui-user-message-content-wrapper flex items-baseline gap-1"
        style={{
          backgroundColor: 'rgba(0, 0, 0, 0.22)',
          borderColor: 'hsl(var(--border))'
        }}
      >
        <span
          className="aui-user-prompt shrink-0 select-none text-[15px] font-medium leading-[1.5]"
          style={{ color: 'hsl(var(--terminal-prompt))' }}
        >
          ›
        </span>
        <div
          className="aui-user-message-content min-w-0 break-words text-[15px] text-foreground"
          style={{ backgroundColor: 'transparent' }}
        >
          <MessagePrimitive.Parts />
        </div>
      </div>

      <div className="ml-3 flex items-center">
        <UserActionBar />
        <BranchPicker className="aui-user-branch-picker" />
      </div>
    </MessagePrimitive.Root>
  )
}

const UserActionBar: FC = () => {
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      className="aui-user-action-bar-root flex items-center"
    >
    </ActionBarPrimitive.Root>
  )
}

const EditComposer: FC = () => {
  return (
    <MessagePrimitive.Root className="aui-edit-composer-wrapper flex w-full flex-col px-2 py-0.5">
      <ComposerPrimitive.Root className="aui-edit-composer-root flex w-full flex-col rounded border border-border bg-muted/30">
        <ComposerPrimitive.Input
          className="aui-edit-composer-input min-h-8 w-full resize-none bg-transparent p-2 text-foreground text-[15px] outline-none"
          autoFocus
        />
        <div className="aui-edit-composer-footer mx-1.5 mb-1.5 flex items-center gap-1 self-end">
          <ComposerPrimitive.Cancel asChild>
            <Button variant="ghost" size="sm" className="h-6 px-2 text-xs">
              Cancel
            </Button>
          </ComposerPrimitive.Cancel>
          <ComposerPrimitive.Send asChild>
            <Button size="sm" className="h-6 px-2 text-xs">
              Update
            </Button>
          </ComposerPrimitive.Send>
        </div>
      </ComposerPrimitive.Root>
    </MessagePrimitive.Root>
  )
}

const BranchPicker: FC<BranchPickerPrimitive.Root.Props> = ({
  className,
  ...rest
}) => {
  return (
    <BranchPickerPrimitive.Root
      hideWhenSingleBranch
      className={cn(
        'aui-branch-picker-root mr-1 -ml-1 inline-flex items-center text-muted-foreground text-[10px]',
        className
      )}
      {...rest}
    >
      <BranchPickerPrimitive.Previous asChild>
        <TooltipIconButton tooltip="Previous">
          <ChevronLeftIcon />
        </TooltipIconButton>
      </BranchPickerPrimitive.Previous>
      <span className="aui-branch-picker-state font-medium">
        <BranchPickerPrimitive.Number /> / <BranchPickerPrimitive.Count />
      </span>
      <BranchPickerPrimitive.Next asChild>
        <TooltipIconButton tooltip="Next">
          <ChevronRightIcon />
        </TooltipIconButton>
      </BranchPickerPrimitive.Next>
    </BranchPickerPrimitive.Root>
  )
}
