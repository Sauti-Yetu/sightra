import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'

export function AppHeader({
  title,
  subtitle,
  backTo,
}: {
  title: string
  subtitle?: string
  backTo?: string
}) {
  return (
    <header className="flex items-start gap-3 px-5 pt-[max(1.25rem,env(safe-area-inset-top))] pb-3">
      {backTo ? (
        <Link
          to={backTo}
          className="mt-1 inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--surface)] text-[var(--text-primary)]"
          aria-label="Go back"
        >
          <ArrowLeft aria-hidden="true" />
        </Link>
      ) : null}
      <div>
        <p className="font-display text-xs font-semibold tracking-[0.22em] text-[var(--accent)]">NURA</p>
        <h1 className="font-display text-2xl font-semibold tracking-tight">{title}</h1>
        {subtitle ? <p className="mt-1 text-[var(--text-secondary)]">{subtitle}</p> : null}
      </div>
    </header>
  )
}
