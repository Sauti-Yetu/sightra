import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Mic, Upload } from 'lucide-react'
import { AnalysisLoader } from '../components/AnalysisLoader'
import { BrandMark } from '../components/BrandMark'
import { CameraView } from '../components/CameraView'
import { CaptureButton } from '../components/CaptureButton'
import { ErrorState } from '../components/ErrorState'
import { ModeSelector } from '../components/ModeSelector'
import { PermissionPrompt } from '../components/PermissionPrompt'
import { StatusChip } from '../components/StatusChip'
import { useCamera } from '../hooks/useCamera'
import { useOnline } from '../hooks/useOnline'
import { announce } from '../accessibility/live'
import { analyzeImage, isAnalysisResult } from '../services/api'
import { captureFromVideo, compressImage } from '../services/image'
import { historyTitle, useHistory } from '../stores/history'
import { useSession } from '../stores/session'
import { useSettings } from '../stores/settings'
import type { ReadMode } from '../types/nura'

export function HomePage() {
  const navigate = useNavigate()
  const online = useOnline()
  const camera = useCamera()
  const fileRef = useRef<HTMLInputElement | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const settings = useSettings()
  const session = useSession()
  const addHistory = useHistory((state) => state.add)
  const [mode, setMode] = useState<ReadMode>(settings.defaultMode)

  useEffect(() => {
    void camera.start()
    return () => {
      abortRef.current?.abort()
      camera.stop()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function runAnalysis(blob: Blob) {
    if (!online) {
      session.setError(
        'Nura is offline. Previously saved content remains available, but visual analysis requires a connection.',
      )
      return
    }
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    session.setLoading(true)
    announce('Reading visual information')
    try {
      const compressed = await compressImage(blob)
      const response = await analyzeImage({
        blob: compressed,
        mode: mode === 'ask' ? 'read' : mode,
        verbosity: settings.verbosity,
        speed: settings.speechSpeed,
        speak: settings.autoPlay,
        sessionId: session.sessionId,
        signal: controller.signal,
      })
      if (!isAnalysisResult(response.result)) {
        throw new Error('missing-result')
      }
      session.setResult(response.result, response.audio?.base64 ?? null, mode)
      addHistory({
        mode,
        title: historyTitle(response.result, mode),
        spoken: response.spoken || response.result.spoken,
        type: response.result.type,
        result: response.result,
        audioBase64: response.audio?.base64 ?? null,
      })
      announce(response.spoken || response.result.spoken)
      navigate('/result')
    } catch (error) {
      if ((error as Error).name === 'AbortError') return
      const message =
        error instanceof Error && error.message && !error.message.includes('missing')
          ? error.message
          : "I couldn't read this clearly. Try moving closer or improving the lighting."
      session.setError(message)
      announce(message)
    }
  }

  async function onRead() {
    const video = camera.videoRef.current
    if (!video) return
    try {
      const blob = await captureFromVideo(video)
      await runAnalysis(blob)
    } catch {
      session.setError("I couldn't read this clearly. Try moving closer or improving the lighting.")
    }
  }

  const modeHint =
    mode === 'currency'
      ? 'Hold a Kenyan note so the face of the bill fills the frame.'
      : mode === 'sign'
        ? 'Center the sign. Street names and room numbers read best up close.'
        : mode === 'document'
          ? 'Fill the frame with the page. Avoid glare on glossy paper.'
          : 'Point your camera at text, signs or documents.'

  return (
    <div className="mx-auto flex min-h-[calc(100dvh-5.5rem)] max-w-6xl flex-col px-4 pb-4 pt-3 lg:grid lg:grid-cols-[minmax(0,1.15fr)_20.5rem] lg:gap-8 lg:pt-6">
      <section className="flex min-h-0 flex-1 flex-col">
        <header className="mb-3 flex items-center justify-between gap-3 pt-[max(0.4rem,env(safe-area-inset-top))]">
          <div className="flex items-center gap-3">
            <BrandMark className="h-11 w-11" />
            <div>
              <p className="font-display text-[0.68rem] font-bold tracking-[0.32em] text-[var(--accent)]">NURA</p>
              <h1 className="font-display text-xl font-semibold leading-none tracking-tight lg:text-2xl">
                AI visual screen reader
              </h1>
            </div>
          </div>
          <StatusChip live={online && !session.loading} label={session.loading ? 'Reading' : online ? 'Ready' : 'Offline'} />
        </header>
        <p className="mb-3 max-lg:sr-only font-display text-lg text-[var(--text-secondary)]">
          See it. Hear it. Understand it.
        </p>

        <div className="relative min-h-0 flex-1">
          {camera.permission === 'granted' ? (
            <CameraView
              videoRef={camera.videoRef}
              torchOn={camera.torchOn}
              torchAvailable={camera.torchAvailable}
              scanning={session.loading}
              onSwitch={() => void camera.switchCamera()}
              onTorch={() => void camera.setTorch(!camera.torchOn)}
            />
          ) : (
            <div className="nura-panel h-[calc(100dvh-12.5rem)] rounded-[1.85rem] lg:h-auto lg:aspect-video">
              <PermissionPrompt
                message={
                  camera.permission === 'unsupported'
                    ? 'This browser cannot access a camera. You can still upload an image.'
                    : camera.error || 'Camera access is required to read visual information.'
                }
                onRequest={() => void camera.start()}
              />
            </div>
          )}
          {session.loading ? <AnalysisLoader /> : null}
          <div className="pointer-events-none absolute inset-x-0 bottom-0 z-10 bg-gradient-to-t from-black via-black/70 to-transparent p-4 pt-20 lg:hidden">
            <div className="pointer-events-auto space-y-3">
              <ModeSelector
                value={mode}
                onChange={(next) => {
                  setMode(next)
                  settings.setMode(next)
                }}
              />
              <CaptureButton
                onClick={() => void onRead()}
                disabled={session.loading || camera.permission !== 'granted'}
              />
            </div>
          </div>
        </div>
      </section>

      <aside className="nura-panel mt-5 hidden flex-col justify-center gap-5 rounded-[1.85rem] p-6 lg:mt-16 lg:flex">
        <p className="font-display text-2xl font-semibold leading-snug">See it. Hear it. Understand it.</p>
        <p className="text-[var(--text-secondary)]">{modeHint}</p>
        <ModeSelector
          value={mode}
          onChange={(next) => {
            setMode(next)
            settings.setMode(next)
          }}
        />
        <CaptureButton onClick={() => void onRead()} disabled={session.loading || camera.permission !== 'granted'} />
        {session.error ? (
          <ErrorState message={session.error} actionLabel="Try again" onAction={() => session.setError(null)} />
        ) : null}
        <SecondaryActions onAsk={() => navigate('/ask')} onUpload={() => fileRef.current?.click()} />
      </aside>

      <div className="mt-3 space-y-3 lg:hidden">
        {session.error ? (
          <ErrorState message={session.error} actionLabel="Try again" onAction={() => session.setError(null)} />
        ) : (
          <p className="text-center text-sm text-[var(--text-secondary)]">{modeHint}</p>
        )}
        <SecondaryActions onAsk={() => navigate('/ask')} onUpload={() => fileRef.current?.click()} />
      </div>
      <input
        ref={fileRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="sr-only"
        aria-label="Upload an image to read"
        onChange={(event) => {
          const file = event.target.files?.[0]
          if (file) void runAnalysis(file)
          event.target.value = ''
        }}
      />
    </div>
  )
}

function SecondaryActions({ onAsk, onUpload }: { onAsk: () => void; onUpload: () => void }) {
  return (
    <div className="flex flex-wrap justify-center gap-3 lg:justify-start">
      <button
        type="button"
        onClick={onAsk}
        className="inline-flex min-h-12 items-center gap-2 rounded-full border border-white/10 bg-white/5 px-5 font-bold"
      >
        <Mic aria-hidden="true" className="h-4 w-4" />
        Ask
      </button>
      <button
        type="button"
        onClick={onUpload}
        className="inline-flex min-h-12 items-center gap-2 rounded-full border border-white/10 bg-white/5 px-5 font-bold"
      >
        <Upload aria-hidden="true" className="h-4 w-4" />
        Upload image
      </button>
    </div>
  )
}
