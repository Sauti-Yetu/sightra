import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { NuraSettings, ReadMode } from '../types/nura'

const defaults: NuraSettings = {
  voiceId: 'default',
  speechSpeed: 1,
  verbosity: 'standard',
  defaultMode: 'read',
  autoPlay: true,
  continuousReading: false,
  retainImages: false,
  textSize: 'standard',
  highContrast: false,
  reducedMotion: false,
}

interface SettingsState extends NuraSettings {
  setSetting: <K extends keyof NuraSettings>(key: K, value: NuraSettings[K]) => void
  setMode: (mode: ReadMode) => void
}

export const useSettings = create<SettingsState>()(
  persist(
    (set) => ({
      ...defaults,
      setSetting: (key, value) => set({ [key]: value }),
      setMode: (defaultMode) => set({ defaultMode }),
    }),
    { name: 'nura-settings' },
  ),
)
