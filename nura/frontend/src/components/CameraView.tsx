import type { ReactNode, RefObject } from 'react'
import { Flashlight, SwitchCamera, X } from 'lucide-react'
import { ScanOverlay } from './ScanOverlay'

export function CameraView({
  videoRef,
  torchOn,
  torchAvailable,
  scanning,
  onSwitch,
  onTorch,
  onClose,
}: {
  videoRef: RefObject<HTMLVideoElement | null>
  torchOn: boolean
  torchAvailable: boolean
  scanning?: boolean
  onSwitch: () => void
  onTorch: () => void
  onClose?: () => void
}) {
  return (
    <div className="relative aspect-[3/4] w-full overflow-hidden rounded-[1.85rem] border border-white/10 bg-black shadow-[0_30px_80px_rgba(0,0,0,0.45)] max-lg:aspect-auto max-lg:h-[calc(100dvh-12.5rem)] md:aspect-video max-lg:md:aspect-auto">
      <video
        ref={videoRef}
        className="h-full w-full object-cover"
        playsInline
        muted
        autoPlay
        aria-label="Camera preview"
      />
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/55 via-transparent to-black/25" />
      <ScanOverlay scanning={scanning} />
      <div className="absolute right-3 top-3 flex flex-col gap-2">
        <IconButton label="Switch camera" onClick={onSwitch}>
          <SwitchCamera aria-hidden="true" />
        </IconButton>
        {torchAvailable ? (
          <IconButton
            label={torchOn ? 'Turn flashlight off' : 'Turn flashlight on'}
            pressed={torchOn}
            onClick={onTorch}
          >
            <Flashlight aria-hidden="true" />
          </IconButton>
        ) : null}
        {onClose ? (
          <IconButton label="Close camera" onClick={onClose}>
            <X aria-hidden="true" />
          </IconButton>
        ) : null}
      </div>
    </div>
  )
}

function IconButton({
  label,
  onClick,
  pressed,
  children,
}: {
  label: string
  onClick: () => void
  pressed?: boolean
  children: ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      aria-pressed={pressed}
      className={[
        'inline-flex h-12 w-12 items-center justify-center rounded-full border border-white/15 bg-black/55 text-white backdrop-blur-md',
        pressed ? 'bg-[var(--accent)] text-background' : '',
      ].join(' ')}
    >
      {children}
    </button>
  )
}
