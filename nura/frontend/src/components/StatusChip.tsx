export function StatusChip({
  live,
  label,
}: {
  live: boolean
  label: string
}) {
  return (
    <span className="nura-chip" role="status">
      <span
        className="nura-chip-dot"
        style={{ background: live ? "var(--accent)" : "var(--danger)", boxShadow: live ? undefined : "none" }}
      />
      {label}
    </span>
  )
}
