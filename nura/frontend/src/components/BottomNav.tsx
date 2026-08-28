import { Camera, History, Settings } from 'lucide-react'
import { NavLink } from 'react-router-dom'

const items = [
  { to: '/', label: 'Scan', icon: Camera, end: true },
  { to: '/history', label: 'History', icon: History, end: false },
  { to: '/settings', label: 'Settings', icon: Settings, end: false },
]

export function BottomNav() {
  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-0 bottom-0 z-30 border-t border-[var(--border)] bg-[var(--surface)]/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-md"
    >
      <ul className="mx-auto grid max-w-lg grid-cols-3">
        {items.map((item) => (
          <li key={item.to}>
            <NavLink
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                [
                  'flex min-h-16 flex-col items-center justify-center gap-1 px-2 text-sm font-bold',
                  isActive ? 'text-[var(--accent)]' : 'text-[var(--text-secondary)]',
                ].join(' ')
              }
            >
              <item.icon aria-hidden="true" className="h-6 w-6" />
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  )
}
