import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { BottomNav } from './components/BottomNav'
import { InstallPrompt } from './components/InstallPrompt'
import { OfflineBanner } from './components/OfflineBanner'
import { AskPage } from './pages/AskPage'
import { HistoryPage } from './pages/HistoryPage'
import { HomePage } from './pages/HomePage'
import { ReadPage } from './pages/ReadPage'
import { ResultPage } from './pages/ResultPage'
import { SettingsPage } from './pages/SettingsPage'
import { useSettings } from './stores/settings'

export default function App() {
  const { highContrast, reducedMotion, textSize } = useSettings()

  useEffect(() => {
    const root = document.documentElement
    root.classList.toggle('nura-high-contrast', highContrast)
    root.classList.toggle('nura-reduced-motion', reducedMotion)
    root.classList.toggle('nura-text-large', textSize === 'large')
    root.classList.toggle('nura-text-xl', textSize === 'xl')
  }, [highContrast, reducedMotion, textSize])

  return (
    <BrowserRouter>
      <div className="min-h-dvh bg-[var(--background)] pb-24 text-[var(--text-primary)]">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-xl focus:bg-[var(--accent)] focus:px-4 focus:py-2 focus:text-background"
        >
          Skip to content
        </a>
        <OfflineBanner />
        <InstallPrompt />
        <main id="main">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/read" element={<ReadPage />} />
            <Route path="/result" element={<ResultPage />} />
            <Route path="/ask" element={<AskPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <div id="nura-live" className="sr-only" aria-live="polite" aria-atomic="true" />
        <BottomNav />
      </div>
    </BrowserRouter>
  )
}
