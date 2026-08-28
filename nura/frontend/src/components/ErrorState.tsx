import { AlertCircle } from 'lucide-react'

export function ErrorState({
  message,
  actionLabel,
  onAction,
}: {
  message: string
  actionLabel?: string
  onAction?: () => void
}) {
  return (
    <div role="alert" className="rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-5">
      <div className="flex items-start gap-3">
        <AlertCircle aria-hidden="true" className="mt-0.5 h-6 w-6 text-[var(--danger)]" />
        <div>
          <p className="font-bold">Something needs your attention</p>
          <p className="mt-1 text-[var(--text-secondary)]">{message}</p>
          {onAction && actionLabel ? (
            <button
              type="button"
              onClick={onAction}
              className="mt-4 min-h-12 rounded-2xl bg-[var(--accent)] px-4 font-bold text-background"
            >
              {actionLabel}
            </button>
          ) : null}
        </div>
      </div>
    </div>
  )
}
