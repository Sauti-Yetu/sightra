import { useEffect, useState } from 'react'
import { Download } from 'lucide-react'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

export function InstallPrompt() {
  const [event, setEvent] = useState<BeforeInstallPromptEvent | null>(null)
  const [hidden, setHidden] = useState(() => localStorage.getItem('nura-install-dismissed') === '1')

  useEffect(() => {
    const handler = (incoming: Event) => {
      incoming.preventDefault()
      setEvent(incoming as BeforeInstallPromptEvent)
    }
    window.addEventListener('beforeinstallprompt', handler)
    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  if (!event || hidden) return null

  return (
    <div className="mx-4 mb-3 flex items-center gap-3 rounded-3xl border border-[var(--border)] bg-[var(--surface-elevated)] p-4">
      <Download aria-hidden="true" className="h-6 w-6 text-[var(--accent)]" />
      <p className="flex-1 font-bold">Install Nura on this device</p>
      <button
        type="button"
        className="rounded-full bg-[var(--accent)] px-4 font-bold text-background"
        onClick={async () => {
          await event.prompt()
          setEvent(null)
        }}
      >
        Install
      </button>
      <button
        type="button"
        className="rounded-full px-3 text-sm text-[var(--text-secondary)]"
        onClick={() => {
          localStorage.setItem('nura-install-dismissed', '1')
          setHidden(true)
        }}
      >
        Not now
      </button>
    </div>
  )
}
