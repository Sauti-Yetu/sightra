import type { ReactNode } from 'react'

export function SettingsSection({
  title,
  children,
}: {
  title: string
  children: ReactNode
}) {
  return (
    <section className="nura-panel rounded-[1.75rem] p-5">
      <h2 className="mb-4 font-display text-xl font-semibold">{title}</h2>
      <div className="space-y-4">{children}</div>
    </section>
  )
}

export function SettingRow({
  label,
  description,
  children,
}: {
  label: string
  description?: string
  children: ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div>
        <p className="font-bold">{label}</p>
        {description ? <p className="text-sm text-[var(--text-secondary)]">{description}</p> : null}
      </div>
      {children}
    </div>
  )
}
