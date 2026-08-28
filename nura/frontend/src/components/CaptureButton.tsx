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
      className="mx-auto flex min-h-20 min-w-52 items-center justify-center gap-3 rounded-full bg-[var(--accent)] px-10 text-2xl font-bold text-background shadow-[0_12px_40px_rgba(78,224,184,0.28)] disabled:opacity-50"
    >
      <ScanLine aria-hidden="true" className="h-8 w-8" />
      {label}
    </button>
  )
}
