import { useState } from 'react'
import { VoiceButton } from './VoiceButton'

export function AskInput({
  recording,
  disabled,
  onSubmitText,
  onToggleVoice,
}: {
  recording: boolean
  disabled?: boolean
  onSubmitText: (question: string) => void
  onToggleVoice: () => void
}) {
  const [value, setValue] = useState('')
  return (
    <form
      className="nura-panel space-y-3 rounded-[1.75rem] p-5"
      onSubmit={(event) => {
        event.preventDefault()
        const next = value.trim()
        if (!next) return
        onSubmitText(next)
        setValue('')
      }}
    >
      <label htmlFor="nura-ask" className="font-display text-lg font-semibold">
        Ask about this
      </label>
      <textarea
        id="nura-ask"
        value={value}
        disabled={disabled}
        onChange={(event) => setValue(event.target.value)}
        placeholder="When is the deadline?"
        className="min-h-28 w-full rounded-3xl border border-white/10 bg-black/25 px-4 py-3 text-lg"
      />
      <div className="flex flex-wrap gap-3">
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="min-h-14 rounded-full bg-[var(--accent)] px-6 font-bold text-background disabled:opacity-50"
        >
          Ask
        </button>
        <VoiceButton recording={recording} onClick={onToggleVoice} label="Ask with voice" />
      </div>
    </form>
  )
}
