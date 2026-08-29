import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'
import { BrandMark } from './BrandMark'

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
    <header className="flex items-start gap-3 px-1 pt-[max(1.15rem,env(safe-area-inset-top))] pb-4">
      {backTo ? (
        <Link
          to={backTo}
          className="mt-1 inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-[var(--text-primary)]"
          aria-label="Go back"
        >
          <ArrowLeft aria-hidden="true" />
        </Link>
      ) : (
        <BrandMark className="mt-1 h-11 w-11" />
      )}
      <div>
        <p className="font-display text-[0.7rem] font-bold tracking-[0.28em] text-[var(--accent)]">NURA</p>
        <h1 className="font-display text-[1.7rem] font-semibold leading-tight tracking-tight">{title}</h1>
        {subtitle ? <p className="mt-1 max-w-md text-[var(--text-secondary)]">{subtitle}</p> : null}
      </div>
    </header>
  )
}
