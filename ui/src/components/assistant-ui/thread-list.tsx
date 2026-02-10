import {
  AuiIf,
  ThreadListItemMorePrimitive,
  ThreadListItemPrimitive,
  ThreadListPrimitive,
  useAssistantApi
} from '@assistant-ui/react'
import { ArchiveIcon, MoreHorizontalIcon, PencilIcon, TrashIcon } from 'lucide-react'
import { useCallback } from 'react'
import type { FC } from 'react'

import { Button } from '@/components/ui/button'

export const ThreadList: FC = () => {
  return (
    <ThreadListPrimitive.Root className="aui-root aui-thread-list-root flex flex-row items-center h-8 border-b border-border overflow-x-auto gap-0.5 px-1">
      <AuiIf condition={({ threads }) => !threads.isLoading}>
        <ThreadListPrimitive.Items components={{ ThreadListItem }} />
      </AuiIf>
    </ThreadListPrimitive.Root>
  )
}

const ThreadListItem: FC = () => {
  return (
    <ThreadListItemPrimitive.Root className="aui-thread-list-item group inline-flex h-7 items-center gap-0.5 rounded px-2 text-xs transition-colors hover:bg-muted focus-visible:bg-muted focus-visible:outline-none data-active:bg-accent data-active:text-accent-foreground">
      <ThreadListItemPrimitive.Trigger className="aui-thread-list-item-trigger inline-flex h-full min-w-0 max-w-[120px] items-center truncate text-start text-xs">
        <ThreadListItemPrimitive.Title fallback="New Chat" />
      </ThreadListItemPrimitive.Trigger>
      <ThreadListItemMore />
    </ThreadListItemPrimitive.Root>
  )
}

const ThreadListItemMore: FC = () => {
  const api = useAssistantApi()

  const handleRename = useCallback(() => {
    const item = api.threadListItem()
    const state = item.getState()
    const currentTitle = state.title || 'New Chat'
    const newTitle = window.prompt('Rename session', currentTitle)
    if (newTitle !== null && newTitle.trim()) {
      item.rename(newTitle.trim())
    }
  }, [api])

  return (
    <ThreadListItemMorePrimitive.Root>
      <ThreadListItemMorePrimitive.Trigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="aui-thread-list-item-more size-4 p-0 opacity-0 transition-opacity group-hover:opacity-100 data-[state=open]:opacity-100 group-data-active:opacity-100"
        >
          <MoreHorizontalIcon className="size-3" />
          <span className="sr-only">More options</span>
        </Button>
      </ThreadListItemMorePrimitive.Trigger>
      <ThreadListItemMorePrimitive.Content
        side="bottom"
        align="start"
        className="aui-thread-list-item-more-content z-50 min-w-28 overflow-hidden rounded border bg-popover p-0.5 text-popover-foreground shadow-md"
      >
        <ThreadListItemMorePrimitive.Item
          className="aui-thread-list-item-more-item flex cursor-pointer select-none items-center gap-1.5 rounded-sm px-2 py-1 text-xs outline-none hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground"
          onSelect={handleRename}
        >
          <PencilIcon className="size-3" />
          Rename
        </ThreadListItemMorePrimitive.Item>
        <ThreadListItemPrimitive.Archive asChild>
          <ThreadListItemMorePrimitive.Item className="aui-thread-list-item-more-item flex cursor-pointer select-none items-center gap-1.5 rounded-sm px-2 py-1 text-xs outline-none hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground">
            <ArchiveIcon className="size-3" />
            Archive
          </ThreadListItemMorePrimitive.Item>
        </ThreadListItemPrimitive.Archive>
        <ThreadListItemPrimitive.Delete asChild>
          <ThreadListItemMorePrimitive.Item className="aui-thread-list-item-more-item flex cursor-pointer select-none items-center gap-1.5 rounded-sm px-2 py-1 text-destructive text-xs outline-none hover:bg-destructive/10 hover:text-destructive focus:bg-destructive/10 focus:text-destructive">
            <TrashIcon className="size-3" />
            Delete
          </ThreadListItemMorePrimitive.Item>
        </ThreadListItemPrimitive.Delete>
      </ThreadListItemMorePrimitive.Content>
    </ThreadListItemMorePrimitive.Root>
  )
}
