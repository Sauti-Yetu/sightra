import { ScanLine } from 'lucide-react'

export function CaptureButton({
  onClick,
  disabled,
  label = 'Read',
}: {
  onClick: () => void
  disabled?: boolean
  label?: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="group relative mx-auto flex min-h-[4.75rem] min-w-56 items-center justify-center gap-3 rounded-full bg-[var(--accent)] px-8 text-2xl font-bold tracking-tight text-background shadow-[0_16px_50px_var(--glow)] transition enabled:hover:brightness-105 disabled:opacity-45"
    >
      <span className="nura-ring absolute inset-0 rounded-full border border-[var(--accent)]" aria-hidden="true" />
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-black/15">
        <ScanLine aria-hidden="true" className="h-6 w-6" />
      </span>
      {label}
    </button>
  )
}
