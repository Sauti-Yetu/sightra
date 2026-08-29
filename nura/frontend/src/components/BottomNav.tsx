import { Camera, History, Settings } from 'lucide-react'
import { NavLink } from 'react-router-dom'

const items = [
  { to: '/', label: 'Scan', icon: Camera, end: true },
  { to: '/history', label: 'History', icon: History, end: false },
  { to: '/settings', label: 'Settings', icon: Settings, end: false },
]

export function BottomNav() {
  return (
    <nav aria-label="Primary" className="pointer-events-none fixed inset-x-0 bottom-0 z-30 px-4 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
      <ul className="nura-panel pointer-events-auto mx-auto grid max-w-md grid-cols-3 rounded-[1.6rem] p-1.5">
        {items.map((item) => (
          <li key={item.to}>
            <NavLink
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                [
                  'flex min-h-14 flex-col items-center justify-center gap-1 rounded-[1.2rem] px-2 text-xs font-bold tracking-wide transition',
                  isActive
                    ? 'bg-[var(--accent)] text-background shadow-[0_8px_24px_var(--glow)]'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]',
                ].join(' ')
              }
            >
              <item.icon aria-hidden="true" className="h-5 w-5" />
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  )
}
