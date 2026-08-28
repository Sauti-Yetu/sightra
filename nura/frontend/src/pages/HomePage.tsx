import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Mic, Upload } from 'lucide-react'
import { AnalysisLoader } from '../components/AnalysisLoader'
import { CameraView } from '../components/CameraView'
import { CaptureButton } from '../components/CaptureButton'
import { ErrorState } from '../components/ErrorState'
import { ModeSelector } from '../components/ModeSelector'
import { PermissionPrompt } from '../components/PermissionPrompt'
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

  return (
    <div className="mx-auto flex min-h-[calc(100dvh-5.5rem)] max-w-5xl flex-col px-4 pb-4 pt-3 lg:grid lg:grid-cols-[minmax(0,1.1fr)_minmax(18rem,0.9fr)] lg:gap-8 lg:pt-8">
      <section className="flex min-h-0 flex-1 flex-col">
        <header className="mb-3 text-center lg:text-left">
          <p className="font-display text-xs font-semibold tracking-[0.28em] text-[var(--accent)]">NURA</p>
          <h1 className="font-display text-3xl font-semibold tracking-tight">AI visual screen reader</h1>
          <p className="mt-1 text-[var(--text-secondary)]">See it. Hear it. Understand it.</p>
        </header>

        <div className="relative min-h-0 flex-1">
          {camera.permission === 'granted' ? (
            <CameraView
              videoRef={camera.videoRef}
              torchOn={camera.torchOn}
              torchAvailable={camera.torchAvailable}
              onSwitch={() => void camera.switchCamera()}
              onTorch={() => void camera.setTorch(!camera.torchOn)}
            />
          ) : (
            <div className="h-[calc(100dvh-13.5rem)] rounded-[2rem] bg-[var(--surface)] lg:h-auto lg:aspect-video">
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
          <div className="pointer-events-none absolute inset-x-0 bottom-0 z-10 bg-gradient-to-t from-black/80 to-transparent p-4 pt-16 lg:hidden">
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

      <section className="mt-4 flex flex-col gap-4 max-lg:hidden lg:mt-16">
        <ModeSelector
          value={mode}
          onChange={(next) => {
            setMode(next)
            settings.setMode(next)
          }}
        />
        <CaptureButton onClick={() => void onRead()} disabled={session.loading || camera.permission !== 'granted'} />
        <p className="text-[var(--text-secondary)]">Point your camera at text, signs or documents.</p>
        {session.error ? (
          <ErrorState message={session.error} actionLabel="Try again" onAction={() => session.setError(null)} />
        ) : null}
        <div className="mt-2 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => navigate('/ask')}
            className="inline-flex min-h-12 items-center gap-2 rounded-full bg-[var(--surface-elevated)] px-5 font-bold"
          >
            <Mic aria-hidden="true" className="h-4 w-4" />
            Ask
          </button>
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className="inline-flex min-h-12 items-center gap-2 rounded-full bg-[var(--surface-elevated)] px-5 font-bold"
          >
            <Upload aria-hidden="true" className="h-4 w-4" />
            Upload image
          </button>
        </div>
      </section>
      <div className="mt-3 flex flex-wrap justify-center gap-3 lg:hidden">
        {session.error ? (
          <div className="w-full">
            <ErrorState message={session.error} actionLabel="Try again" onAction={() => session.setError(null)} />
          </div>
        ) : (
          <p className="w-full text-center text-sm text-[var(--text-secondary)]">
            Point your camera at text, signs or documents.
          </p>
        )}
        <button
          type="button"
          onClick={() => navigate('/ask')}
          className="inline-flex min-h-12 items-center gap-2 rounded-full bg-[var(--surface-elevated)] px-5 font-bold"
        >
          <Mic aria-hidden="true" className="h-4 w-4" />
          Ask
        </button>
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          className="inline-flex min-h-12 items-center gap-2 rounded-full bg-[var(--surface-elevated)] px-5 font-bold"
        >
          <Upload aria-hidden="true" className="h-4 w-4" />
          Upload image
        </button>
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
