import { useNavigate } from 'react-router-dom'
import { AppHeader } from '../components/AppHeader'
import { HistoryItem } from '../components/HistoryItem'
import { useHistory } from '../stores/history'
import { useSession } from '../stores/session'

export function HistoryPage() {
  const navigate = useNavigate()
  const { items, remove } = useHistory()
  const setResult = useSession((state) => state.setResult)

  return (
    <div className="mx-auto max-w-2xl px-4 py-4">
      <AppHeader title="History" subtitle="Recent readings. Images are not stored." />
      {items.length === 0 ? (
        <p className="mt-6 text-[var(--text-secondary)]">No scans yet. Capture text, a sign, or a document to begin.</p>
      ) : (
        <ul className="mt-4 space-y-3">
          {items.map((item) => (
            <li key={item.id}>
              <HistoryItem
                item={item}
                onOpen={() => {
                  setResult(item.result, item.audioBase64, item.mode)
                  navigate('/result')
                }}
                onDelete={() => remove(item.id)}
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
