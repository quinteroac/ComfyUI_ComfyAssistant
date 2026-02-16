import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Strip backend-injected local HTML comments from message text so they are not shown in the UI. */
export function stripLocalMessageComments(text: string): string {
  if (!text || typeof text !== 'string') return text
  let out = text.replace(/^<!-- local:slash -->\n?/, '')
  out = out.replace(/\s*<!--\s*local:persona-create\s*[^]*?-->\s*$/, '')
  return out
}
