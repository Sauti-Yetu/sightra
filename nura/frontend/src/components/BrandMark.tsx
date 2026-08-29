export function BrandMark({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 64 64" aria-hidden="true">
      <rect width="64" height="64" rx="18" fill="#12161e" />
      <path
        d="M12 38c8-16 32-16 40 0"
        fill="none"
        stroke="#5ef0c8"
        strokeWidth="4"
        strokeLinecap="round"
      />
      <path
        d="M20 34c5-8 19-8 24 0"
        fill="none"
        stroke="#5ef0c8"
        strokeWidth="3"
        strokeLinecap="round"
        opacity="0.55"
      />
      <circle cx="32" cy="40" r="5" fill="#f4f6f8" />
    </svg>
  )
}
