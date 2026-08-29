import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Pause, Play, Repeat, Square } from 'lucide-react'
import { synthesizeSpeech } from '../services/api'

export function AudioPlayer({
  src,
  spokenText,
  autoPlay,
  speed,
  onEnded,
}: {
  src: string | null
  spokenText?: string
  autoPlay?: boolean
  speed: number
  onEnded?: () => void
}) {
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const objectUrlRef = useRef<string | null>(null)
  const [resolvedSrc, setResolvedSrc] = useState<string | null>(src)
  const [playing, setPlaying] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let cancelled = false

    async function prepare() {
      window.speechSynthesis?.cancel()
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current)
        objectUrlRef.current = null
      }

      if (src) {
        setResolvedSrc(src)
        if (autoPlay) playUrl(src)
        else setPlaying(false)
        return
      }

      if (!spokenText) {
        setResolvedSrc(null)
        return
      }

      setLoading(true)
      try {
        const blob = await synthesizeSpeech(spokenText, speed)
        if (cancelled) return
        const url = URL.createObjectURL(blob)
        objectUrlRef.current = url
        setResolvedSrc(url)
        if (autoPlay) playUrl(url, false)
      } catch {
        if (!cancelled && autoPlay) speakFallback()
        else setResolvedSrc(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void prepare()
    return () => {
      cancelled = true
      window.speechSynthesis?.cancel()
      audioRef.current?.pause()
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current)
        objectUrlRef.current = null
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [src, spokenText, autoPlay, speed])

  function playUrl(url: string, applyRate = true) {
    const audio = audioRef.current
    if (!audio) return
    audio.pause()
    audio.src = url
    audio.playbackRate = applyRate && !objectUrlRef.current ? speed : 1
    audio.play().then(() => setPlaying(true)).catch(() => speakFallback())
  }

  function speakFallback() {
    if (!spokenText || !window.speechSynthesis) return
    const utterance = new SpeechSynthesisUtterance(spokenText)
    utterance.rate = speed
    utterance.onend = () => {
      setPlaying(false)
      onEnded?.()
    }
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(utterance)
    setPlaying(true)
  }

  const play = () => {
    if (resolvedSrc) {
      playUrl(resolvedSrc, !objectUrlRef.current && !src)
      return
    }
    if (spokenText) {
      setLoading(true)
      void synthesizeSpeech(spokenText, speed)
        .then((blob) => {
          const url = URL.createObjectURL(blob)
          if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current)
          objectUrlRef.current = url
          setResolvedSrc(url)
          playUrl(url, false)
        })
        .catch(() => speakFallback())
        .finally(() => setLoading(false))
    }
  }

  const pause = () => {
    window.speechSynthesis?.pause()
    audioRef.current?.pause()
    setPlaying(false)
  }

  const stop = () => {
    window.speechSynthesis?.cancel()
    const audio = audioRef.current
    if (audio) {
      audio.pause()
      audio.currentTime = 0
    }
    setPlaying(false)
  }

  const repeat = () => {
    stop()
    play()
  }

  const enabled = Boolean(src || spokenText || resolvedSrc)

  return (
    <div className="nura-panel rounded-[1.75rem] p-5">
      <audio
        ref={audioRef}
        className="sr-only"
        onEnded={() => {
          setPlaying(false)
          onEnded?.()
        }}
      />
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="text-[0.7rem] font-bold uppercase tracking-[0.18em] text-[var(--accent)]">Voice</p>
          <p className="font-display text-xl font-semibold">
            {loading ? 'Preparing voice…' : playing ? 'Speaking' : 'Listen'}
          </p>
        </div>
        <div className="flex h-10 items-end gap-1" aria-hidden="true">
          {[0, 1, 2, 3, 4].map((i) => (
            <span
              key={i}
              className={['w-1.5 rounded-full bg-[var(--accent)]', playing ? 'nura-wave' : ''].join(' ')}
              style={{
                height: `${10 + (i % 3) * 8}px`,
                animationDelay: `${i * 0.12}s`,
                opacity: playing ? 1 : 0.35,
              }}
            />
          ))}
        </div>
      </div>
      <div className="grid grid-cols-4 gap-2">
        <Control onClick={play} label="Play spoken result" disabled={!enabled || loading}>
          <Play aria-hidden="true" />
          Play
        </Control>
        <Control onClick={pause} label="Pause spoken result" disabled={!playing}>
          <Pause aria-hidden="true" />
          Pause
        </Control>
        <Control onClick={repeat} label="Repeat spoken result" disabled={!enabled || loading}>
          <Repeat aria-hidden="true" />
          Repeat
        </Control>
        <Control onClick={stop} label="Stop spoken result" disabled={!enabled}>
          <Square aria-hidden="true" />
          Stop
        </Control>
      </div>
    </div>
  )
}

function Control({
  onClick,
  label,
  disabled,
  children,
}: {
  onClick: () => void
  label: string
  disabled?: boolean
  children: ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      disabled={disabled}
      className="flex min-h-[3.4rem] flex-col items-center justify-center gap-1 rounded-2xl border border-white/10 bg-white/5 text-[0.75rem] font-bold disabled:opacity-35"
    >
      {children}
    </button>
  )
}
