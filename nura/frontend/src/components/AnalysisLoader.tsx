export function AnalysisLoader({ label = 'Reading visual information' }: { label?: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-4 rounded-[1.85rem] bg-black/72 px-6 text-center backdrop-blur-[2px]"
    >
      <div className="relative">
        <div className="nura-ring absolute inset-[-8px] rounded-full border border-[var(--accent)]" />
        <div className="nura-loader h-16 w-16 rounded-full border-4 border-[var(--accent)]/25 border-t-[var(--accent)]" />
      </div>
      <p className="font-display text-2xl font-semibold">{label}</p>
      <p className="text-[var(--text-secondary)]">Keep the page or sign in view.</p>
    </div>
  )
}
