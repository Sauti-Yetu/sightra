import type { RefObject } from 'react'
import { Flashlight, SwitchCamera, X } from 'lucide-react'
import { ScanOverlay } from './ScanOverlay'

export function CameraView({
  videoRef,
  torchOn,
  torchAvailable,
  onSwitch,
  onTorch,
  onClose,
}: {
  videoRef: RefObject<HTMLVideoElement | null>
  torchOn: boolean
  torchAvailable: boolean
  onSwitch: () => void
  onTorch: () => void
  onClose?: () => void
}) {
  return (
    <div className="relative aspect-[3/4] w-full overflow-hidden rounded-[2rem] bg-black max-lg:aspect-auto max-lg:h-[calc(100dvh-13.5rem)] md:aspect-video max-lg:md:aspect-auto">
      <video
        ref={videoRef}
        className="h-full w-full object-cover"
        playsInline
        muted
        autoPlay
        aria-label="Camera preview"
      />
      <ScanOverlay />
      <div className="absolute right-3 top-3 flex flex-col gap-2">
        <button
          type="button"
          onClick={onSwitch}
          className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-black/55 text-white"
          aria-label="Switch camera"
        >
          <SwitchCamera aria-hidden="true" />
        </button>
        {torchAvailable ? (
          <button
            type="button"
            onClick={onTorch}
            aria-pressed={torchOn}
            className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-black/55 text-white"
            aria-label={torchOn ? 'Turn flashlight off' : 'Turn flashlight on'}
          >
            <Flashlight aria-hidden="true" />
          </button>
        ) : null}
        {onClose ? (
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-black/55 text-white"
            aria-label="Close camera"
          >
            <X aria-hidden="true" />
          </button>
        ) : null}
      </div>
    </div>
  )
}
