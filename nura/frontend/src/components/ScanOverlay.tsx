export function ScanOverlay() {
  return (
    <div className="pointer-events-none absolute inset-4" aria-hidden="true">
      <span className="absolute left-0 top-0 h-10 w-10 rounded-tl-3xl border-l-4 border-t-4 border-[var(--accent)]" />
      <span className="absolute right-0 top-0 h-10 w-10 rounded-tr-3xl border-r-4 border-t-4 border-[var(--accent)]" />
      <span className="absolute bottom-0 left-0 h-10 w-10 rounded-bl-3xl border-b-4 border-l-4 border-[var(--accent)]" />
      <span className="absolute bottom-0 right-0 h-10 w-10 rounded-br-3xl border-b-4 border-r-4 border-[var(--accent)]" />
    </div>
  )
}
