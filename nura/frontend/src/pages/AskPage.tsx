import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppHeader } from '../components/AppHeader'
import { AskInput } from '../components/AskInput'
import { AudioPlayer } from '../components/AudioPlayer'
import { ErrorState } from '../components/ErrorState'
import { useSpeechRecorder } from '../hooks/useSpeechRecorder'
import { announce } from '../accessibility/live'
import { askQuestion } from '../services/api'
import { dataUrlFromBase64 } from '../services/image'
import { useSession } from '../stores/session'
import { useSettings } from '../stores/settings'

export function AskPage() {
  const navigate = useNavigate()
  const recorder = useSpeechRecorder()
  const session = useSession()
  const settings = useSettings()
  const [answer, setAnswer] = useState<string | null>(null)
  const [audio, setAudio] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(question?: string, audioBlob?: Blob) {
    if (!session.lastResult) {
      session.setError('I don\'t have a recent scan to answer from. Capture the visual information first.')
      return
    }
    setBusy(true)
    announce('Thinking about your question')
    try {
      const response = await askQuestion({
        question,
        audio: audioBlob,
        verbosity: settings.verbosity,
        speed: settings.speechSpeed,
        speak: settings.autoPlay,
        sessionId: session.sessionId,
      })
      const spoken = response.spoken || ''
      setAnswer(spoken)
      setAudio(response.audio?.base64 ?? null)
      announce(spoken)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'I couldn\'t hear that clearly. Please try speaking again.'
      session.setError(message)
      announce(message)
    } finally {
      setBusy(false)
    }
  }

  async function toggleVoice() {
    if (recorder.recording) {
      const blob = await recorder.stop()
      if (blob) await submit(undefined, blob)
      return
    }
    await recorder.start()
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-4">
      <AppHeader title="Ask" subtitle="Questions use your current scan. You do not need to capture again." backTo="/result" />
      {!session.lastResult ? (
        <ErrorState
          message="Capture visual information first, then ask a follow-up question."
          actionLabel="New scan"
          onAction={() => navigate('/')}
        />
      ) : (
        <div className="space-y-5">
          <p className="rounded-3xl bg-[var(--surface)] p-4 text-[var(--text-secondary)]">
            Current scan: {session.lastResult.title || session.lastResult.summary || 'Recent visual information'}
          </p>
          <AskInput
            recording={recorder.recording}
            disabled={busy}
            onSubmitText={(question) => void submit(question)}
            onToggleVoice={() => void toggleVoice()}
          />
          {recorder.error ? <ErrorState message={recorder.error} /> : null}
          {session.error ? <ErrorState message={session.error} /> : null}
          {answer ? (
            <section className="space-y-3 rounded-[1.75rem] border border-[var(--border)] bg-[var(--surface)] p-5">
              <h2 className="font-display text-xl font-semibold">Answer</h2>
              <p className="text-lg leading-relaxed">{answer}</p>
              <AudioPlayer
                src={audio ? dataUrlFromBase64(audio) : null}
                spokenText={answer}
                autoPlay={settings.autoPlay}
                speed={settings.speechSpeed}
              />
            </section>
          ) : null}
        </div>
      )}
    </div>
  )
}
