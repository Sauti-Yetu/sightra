import { Camera } from 'lucide-react'

export function PermissionPrompt({
  message,
  onRequest,
}: {
  message: string
  onRequest: () => void
}) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-5 px-6 text-center">
      <div className="flex h-20 w-20 items-center justify-center rounded-full border border-[var(--accent)]/30 bg-[var(--accent-soft)] text-[var(--accent)] shadow-[0_0_40px_var(--glow)]">
        <Camera aria-hidden="true" className="h-10 w-10" />
      </div>
      <p className="max-w-sm text-lg leading-relaxed">{message}</p>
      <button
        type="button"
        onClick={onRequest}
        className="min-h-14 min-w-48 rounded-full bg-[var(--accent)] px-8 text-lg font-bold text-background shadow-[0_12px_32px_var(--glow)]"
      >
        Enable camera
      </button>
    </div>
  )
}
