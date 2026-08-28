export function AnalysisLoader({ label = 'Reading visual information' }: { label?: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-4 rounded-[2rem] bg-black/70 px-6 text-center"
    >
      <div className="nura-loader h-16 w-16 rounded-full border-4 border-[var(--accent)]/30 border-t-[var(--accent)]" />
      <p className="text-xl font-bold">{label}</p>
      <p className="text-[var(--text-secondary)]">Keep the page or sign in view.</p>
    </div>
  )
}
