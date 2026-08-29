import { WifiOff } from 'lucide-react'
import { useOnline } from '../hooks/useOnline'

export function OfflineBanner() {
  const online = useOnline()
  if (online) return null
  return (
    <div
      role="status"
      className="nura-panel mx-4 mt-[max(0.5rem,env(safe-area-inset-top))] flex items-start gap-3 rounded-2xl px-4 py-3"
    >
      <WifiOff aria-hidden="true" className="mt-0.5 h-5 w-5 text-[var(--danger)]" />
      <p>
        Nura is offline. Previously saved content remains available, but visual analysis requires a
        connection.
      </p>
    </div>
  )
}
