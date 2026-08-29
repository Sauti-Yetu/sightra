import { Mic } from 'lucide-react'

export function VoiceButton({
  recording,
  onClick,
  label = 'Ask',
}: {
  recording: boolean
  onClick: () => void
  label?: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={recording}
      className={[
        'inline-flex min-h-14 items-center justify-center gap-2 rounded-full px-6 font-bold',
        recording
          ? 'bg-[var(--danger)] text-white'
          : 'border border-white/10 bg-white/5 text-[var(--text-primary)]',
      ].join(' ')}
    >
      <Mic aria-hidden="true" />
      {recording ? 'Listening — tap to send' : label}
    </button>
  )
}
