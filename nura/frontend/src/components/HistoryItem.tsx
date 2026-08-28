import { Banknote, FileText, ScanLine, Signpost, Trash2 } from 'lucide-react'
import type { HistoryItem as HistoryItemType } from '../types/nura'

export function HistoryItem({
  item,
  onOpen,
  onDelete,
}: {
  item: HistoryItemType
  onOpen: () => void
  onDelete: () => void
}) {
  const Icon = iconFor(item.type)
  return (
    <article className="flex items-start gap-3 rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-4">
      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[var(--accent-soft)] text-[var(--accent)]">
        <Icon aria-hidden="true" />
      </div>
      <button type="button" onClick={onOpen} className="min-w-0 flex-1 text-left">
        <h2 className="truncate font-bold">{item.title}</h2>
        <p className="text-sm text-[var(--text-secondary)]">{relativeTime(item.createdAt)}</p>
        <p className="mt-1 line-clamp-2 text-[var(--text-secondary)]">{item.spoken}</p>
      </button>
      <button
        type="button"
        onClick={onDelete}
        className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--surface-elevated)]"
        aria-label={`Delete ${item.title}`}
      >
        <Trash2 aria-hidden="true" />
      </button>
    </article>
  )
}

function iconFor(type: string) {
  if (type === 'currency') return Banknote
  if (type === 'sign') return Signpost
  if (type === 'document') return FileText
  return ScanLine
}

function relativeTime(timestamp: number): string {
  const delta = Date.now() - timestamp
  const minutes = Math.floor(delta / 60000)
  if (minutes < 1) return 'Just now'
  if (minutes === 1) return '1 minute ago'
  if (minutes < 60) return `${minutes} minutes ago`
  const hours = Math.floor(minutes / 60)
  if (hours === 1) return '1 hour ago'
  if (hours < 24) return `${hours} hours ago`
  return new Date(timestamp).toLocaleDateString()
}
