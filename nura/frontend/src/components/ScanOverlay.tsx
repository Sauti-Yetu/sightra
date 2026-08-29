export function ScanOverlay({ scanning = false }: { scanning?: boolean }) {
  return (
    <div className="pointer-events-none absolute inset-3 overflow-hidden rounded-[1.6rem]" aria-hidden="true">
      <span className="absolute left-0 top-0 h-11 w-11 rounded-tl-3xl border-l-[3px] border-t-[3px] border-[var(--accent)]" />
      <span className="absolute right-0 top-0 h-11 w-11 rounded-tr-3xl border-r-[3px] border-t-[3px] border-[var(--accent)]" />
      <span className="absolute bottom-0 left-0 h-11 w-11 rounded-bl-3xl border-b-[3px] border-l-[3px] border-[var(--accent)]" />
      <span className="absolute bottom-0 right-0 h-11 w-11 rounded-br-3xl border-b-[3px] border-r-[3px] border-[var(--accent)]" />
      <span className="absolute inset-x-8 top-1/2 h-px bg-white/20" />
      <span className="absolute inset-y-8 left-1/2 w-px bg-white/10" />
      {scanning ? (
        <span className="nura-scanline absolute inset-x-6 h-24 bg-gradient-to-b from-transparent via-[var(--accent)] to-transparent opacity-70" />
      ) : null}
    </div>
  )
}
