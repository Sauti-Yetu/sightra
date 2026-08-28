import { useCallback, useRef, useState } from 'react'

export function useSpeechRecorder() {
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<BlobPart[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const [recording, setRecording] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const stop = useCallback(async (): Promise<Blob | null> => {
    const recorder = recorderRef.current
    if (!recorder || recorder.state === 'inactive') {
      streamRef.current?.getTracks().forEach((track) => track.stop())
      setRecording(false)
      return null
    }
    return await new Promise((resolve) => {
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' })
        streamRef.current?.getTracks().forEach((track) => track.stop())
        streamRef.current = null
        recorderRef.current = null
        setRecording(false)
        resolve(blob)
      }
      recorder.stop()
    })
  }, [])

  const start = useCallback(async () => {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false })
      streamRef.current = stream
      const mime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm'
      const recorder = new MediaRecorder(stream, { mimeType: mime })
      chunksRef.current = []
      recorder.ondataavailable = (event) => {
        if (event.data.size) chunksRef.current.push(event.data)
      }
      recorderRef.current = recorder
      recorder.start()
      setRecording(true)
    } catch {
      setError('Microphone access is required to ask a spoken question.')
    }
  }, [])

  return { recording, error, start, stop }
}
