import { useCallback, useEffect, useRef, useState } from 'react'
import { hasTorch, requestCamera, stopStream, toggleTorch } from '../services/camera'

export type PermissionState = 'prompt' | 'granted' | 'denied' | 'unsupported'

export function useCamera() {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [permission, setPermission] = useState<PermissionState>(
    navigator.mediaDevices ? 'prompt' : 'unsupported',
  )
  const [facing, setFacing] = useState<'environment' | 'user'>('environment')
  const [torchOn, setTorchOn] = useState(false)
  const [torchAvailable, setTorchAvailable] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const start = useCallback(async (nextFacing = facing) => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setPermission('unsupported')
      return
    }
    stopStream(streamRef.current)
    streamRef.current = null
    try {
      const stream = await requestCamera(nextFacing)
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play().catch(() => undefined)
      }
      const track = stream.getVideoTracks()[0]
      setTorchAvailable(hasTorch(track))
      setPermission('granted')
      setError(null)
    } catch (caught) {
      const name = (caught as DOMException).name
      if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
        setPermission('denied')
        setError('Camera access is required to read visual information.')
      } else {
        setPermission('denied')
        setError('Camera access is required to read visual information.')
      }
    }
  }, [facing])

  const switchCamera = useCallback(async () => {
    const next = facing === 'environment' ? 'user' : 'environment'
    setFacing(next)
    setTorchOn(false)
    await start(next)
  }, [facing, start])

  const setTorch = useCallback(async (enabled: boolean) => {
    const track = streamRef.current?.getVideoTracks()[0]
    if (!track) return
    const ok = await toggleTorch(track, enabled).catch(() => false)
    if (ok) setTorchOn(enabled)
  }, [])

  const stop = useCallback(() => {
    stopStream(streamRef.current)
    streamRef.current = null
    if (videoRef.current) videoRef.current.srcObject = null
  }, [])

  useEffect(() => {
    return () => stop()
  }, [stop])

  return {
    videoRef,
    permission,
    error,
    facing,
    torchOn,
    torchAvailable,
    start,
    stop,
    switchCamera,
    setTorch,
  }
}
