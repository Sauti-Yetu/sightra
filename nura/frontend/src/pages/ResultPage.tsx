import { Link, useNavigate } from 'react-router-dom'
import { AppHeader } from '../components/AppHeader'
import { AudioPlayer } from '../components/AudioPlayer'
import { ErrorState } from '../components/ErrorState'
import { ResultCard } from '../components/ResultCard'
import { dataUrlFromBase64 } from '../services/image'
import { useSession } from '../stores/session'
import { useSettings } from '../stores/settings'

export function ResultPage() {
  const navigate = useNavigate()
  const { lastResult, lastAudioBase64, error } = useSession()
  const { autoPlay, speechSpeed } = useSettings()

  if (!lastResult) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-6">
        <AppHeader title="Result" backTo="/" />
        <ErrorState
          message="Capture visual information first, then the result will appear here."
          actionLabel="New scan"
          onAction={() => navigate('/')}
        />
      </div>
    )
  }

  const src = lastAudioBase64 ? dataUrlFromBase64(lastAudioBase64) : null

  return (
    <div className="mx-auto grid max-w-6xl gap-5 px-4 py-4 lg:grid-cols-[minmax(0,1.2fr)_22rem]">
      <div>
        <AppHeader title="Result" subtitle="Visual information from your last scan" backTo="/" />
        {error ? <div className="mb-4"><ErrorState message={error} /></div> : null}
        <ResultCard result={lastResult} />
      </div>
      <aside className="space-y-3 pb-10 lg:sticky lg:top-6 lg:self-start lg:pt-16">
        <AudioPlayer src={src} spokenText={lastResult.spoken} autoPlay={autoPlay} speed={speechSpeed} />
        <Link
          to="/ask"
          className="flex min-h-14 items-center justify-center rounded-full bg-[var(--accent)] px-6 font-bold text-background shadow-[0_12px_32px_var(--glow)]"
        >
          Ask about this
        </Link>
        <Link
          to="/"
          className="flex min-h-14 items-center justify-center rounded-full border border-white/10 bg-white/5 px-6 font-bold"
        >
          Read again
        </Link>
        <Link
          to="/"
          className="flex min-h-14 items-center justify-center rounded-full border border-white/10 px-6 font-bold text-[var(--text-secondary)]"
        >
          New scan
        </Link>
      </aside>
    </div>
  )
}
