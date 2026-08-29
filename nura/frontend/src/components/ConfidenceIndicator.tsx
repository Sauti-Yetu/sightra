export function ConfidenceIndicator({ value }: { value: number }) {
  const percent = Math.round(value * 100)
  const label =
    value >= 0.8 ? 'High confidence' : value >= 0.45 ? 'Moderate confidence' : 'Low confidence'
  return (
    <p className="inline-flex items-center gap-2 text-sm text-[var(--text-secondary)]">
      <span className="h-1.5 w-16 overflow-hidden rounded-full bg-white/10" aria-hidden="true">
        <span
          className="block h-full rounded-full bg-[var(--accent)]"
          style={{ width: `${Math.max(8, percent)}%` }}
        />
      </span>
      {label}
      <span className="sr-only"> {percent} percent</span>
    </p>
  )
}
