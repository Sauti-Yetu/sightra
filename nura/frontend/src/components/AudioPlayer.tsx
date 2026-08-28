import { useEffect, useRef, useState } from 'react'
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
    <div className="rounded-3xl bg-[var(--surface-elevated)] p-4">
      <audio
        ref={audioRef}
        className="sr-only"
        onEnded={() => {
          setPlaying(false)
          onEnded?.()
        }}
      />
      <p className="mb-3 font-bold">{loading ? 'Preparing voice…' : 'Voice'}</p>
      <div className="grid grid-cols-4 gap-2">
        <button type="button" onClick={play} className="control-btn" aria-label="Play spoken result" disabled={!enabled || loading}>
          <Play aria-hidden="true" />
          Play
        </button>
        <button type="button" onClick={pause} className="control-btn" aria-label="Pause spoken result" disabled={!playing}>
          <Pause aria-hidden="true" />
          Pause
        </button>
        <button type="button" onClick={repeat} className="control-btn" aria-label="Repeat spoken result" disabled={!enabled || loading}>
          <Repeat aria-hidden="true" />
          Repeat
        </button>
        <button type="button" onClick={stop} className="control-btn" aria-label="Stop spoken result" disabled={!enabled}>
          <Square aria-hidden="true" />
          Stop
        </button>
      </div>
      <style>{`
        .control-btn {
          display: flex;
          min-height: 52px;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 0.2rem;
          border-radius: 1rem;
          background: var(--surface);
          font-size: 0.8rem;
          font-weight: 700;
        }
        .control-btn:disabled { opacity: 0.4; }
      `}</style>
    </div>
  )
}
