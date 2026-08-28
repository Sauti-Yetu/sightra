export function ConfidenceIndicator({ value }: { value: number }) {
  const percent = Math.round(value * 100)
  const label =
    value >= 0.8 ? 'High confidence' : value >= 0.45 ? 'Moderate confidence' : 'Low confidence'
  return (
    <p className="text-sm text-[var(--text-secondary)]">
      {label}
      <span className="sr-only"> {percent} percent</span>
    </p>
  )
}
