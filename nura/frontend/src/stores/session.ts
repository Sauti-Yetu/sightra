import { create } from 'zustand'
import type { AnalysisResult, ReadMode } from '../types/nura'

const SESSION_KEY = 'nura-session-id'

function readSessionId(): string {
  const existing = localStorage.getItem(SESSION_KEY)
  if (existing) return existing
  const id = crypto.randomUUID()
  localStorage.setItem(SESSION_KEY, id)
  return id
}

interface SessionState {
  sessionId: string
  lastResult: AnalysisResult | null
  lastAudioBase64: string | null
  lastMode: ReadMode
  loading: boolean
  error: string | null
  setResult: (result: AnalysisResult, audio: string | null, mode: ReadMode) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearSession: () => void
}

export const useSession = create<SessionState>((set) => ({
  sessionId: typeof window === 'undefined' ? '' : readSessionId(),
  lastResult: null,
  lastAudioBase64: null,
  lastMode: 'read',
  loading: false,
  error: null,
  setResult: (lastResult, lastAudioBase64, lastMode) =>
    set({ lastResult, lastAudioBase64, lastMode, error: null, loading: false }),
  setLoading: (loading) => set(loading ? { loading: true, error: null } : { loading: false }),
  setError: (error) => set({ error, loading: false }),
  clearSession: () => {
    const sessionId = crypto.randomUUID()
    localStorage.setItem(SESSION_KEY, sessionId)
    set({
      sessionId,
      lastResult: null,
      lastAudioBase64: null,
      error: null,
      loading: false,
    })
  },
}))
