export function stopStream(stream: MediaStream | null) {
  stream?.getTracks().forEach((track) => track.stop())
}

export async function requestCamera(facingMode: 'environment' | 'user'): Promise<MediaStream> {
  return navigator.mediaDevices.getUserMedia({
    audio: false,
    video: {
      facingMode: { ideal: facingMode },
      width: { ideal: 1280 },
      height: { ideal: 720 },
    },
  })
}

export async function toggleTorch(track: MediaStreamTrack, enabled: boolean): Promise<boolean> {
  const capabilities = track.getCapabilities?.() as MediaTrackCapabilities & { torch?: boolean }
  if (!capabilities?.torch) return false
  await track.applyConstraints({ advanced: [{ torch: enabled }] as unknown as MediaTrackConstraintSet[] })
  return true
}

export function hasTorch(track: MediaStreamTrack | null): boolean {
  if (!track?.getCapabilities) return false
  const capabilities = track.getCapabilities() as MediaTrackCapabilities & { torch?: boolean }
  return Boolean(capabilities.torch)
}
