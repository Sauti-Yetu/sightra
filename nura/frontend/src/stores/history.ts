import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AnalysisResult, HistoryItem, ReadMode } from '../types/nura'

interface HistoryState {
  items: HistoryItem[]
  add: (item: Omit<HistoryItem, 'id' | 'createdAt'>) => void
  remove: (id: string) => void
  clear: () => void
}

export const useHistory = create<HistoryState>()(
  persist(
    (set) => ({
      items: [],
      add: (item) =>
        set((state) => ({
          items: [
            {
              ...item,
              id: crypto.randomUUID(),
              createdAt: Date.now(),
            },
            ...state.items,
          ].slice(0, 40),
        })),
      remove: (id) => set((state) => ({ items: state.items.filter((item) => item.id !== id) })),
      clear: () => set({ items: [] }),
    }),
    { name: 'nura-history' },
  ),
)

export function historyTitle(result: AnalysisResult, mode: ReadMode): string {
  if (result.title) return result.title
  if (result.type === 'currency' && result.currency?.denomination) {
    return `KES ${result.currency.denomination}`
  }
  if (mode === 'sign') return result.text.split('\n')[0] || 'Sign'
  return result.summary.slice(0, 80) || 'Scan'
}
