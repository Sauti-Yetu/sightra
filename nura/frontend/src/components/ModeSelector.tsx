import type { ReadMode } from '../types/nura'
import { Banknote, FileText, ScanLine, Signpost } from 'lucide-react'

const modes: { id: ReadMode; label: string; icon: typeof ScanLine }[] = [
  { id: 'read', label: 'Read', icon: ScanLine },
  { id: 'currency', label: 'Currency', icon: Banknote },
  { id: 'sign', label: 'Sign', icon: Signpost },
  { id: 'document', label: 'Document', icon: FileText },
]

export function ModeSelector({
  value,
  onChange,
}: {
  value: ReadMode
  onChange: (mode: ReadMode) => void
}) {
  return (
    <div
      role="radiogroup"
      aria-label="Reading mode"
      className="nura-panel flex gap-1 overflow-x-auto rounded-full p-1"
    >
      {modes.map((mode) => {
        const selected = mode.id === value
        return (
          <button
            key={mode.id}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(mode.id)}
            className={[
              'inline-flex min-h-11 shrink-0 items-center gap-2 rounded-full px-3.5 text-sm font-bold transition',
              selected
                ? 'bg-[var(--accent)] text-background'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]',
            ].join(' ')}
          >
            <mode.icon aria-hidden="true" className="h-4 w-4" />
            {mode.label}
          </button>
        )
      })}
    </div>
  )
}
