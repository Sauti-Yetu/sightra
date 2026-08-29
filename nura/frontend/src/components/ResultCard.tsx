import type { AnalysisResult } from '../types/nura'
import { ConfidenceIndicator } from './ConfidenceIndicator'

export function ResultCard({ result }: { result: AnalysisResult }) {
  const heading = result.title || typeLabel(result.type)
  return (
    <article className="nura-panel rounded-[1.85rem] p-6">
      <p className="text-[0.7rem] font-bold uppercase tracking-[0.2em] text-[var(--accent)]">
        {typeLabel(result.type)}
      </p>
      <h2 className="mt-2 font-display text-[1.85rem] font-semibold leading-tight">{heading}</h2>
      <div className="mt-2">
        <ConfidenceIndicator value={result.confidence} />
      </div>
      {result.summary ? (
        <p className="mt-5 text-lg leading-relaxed text-[var(--text-primary)]">{result.summary}</p>
      ) : null}
      {result.important_information.length > 0 ? (
        <ul className="mt-5 space-y-2">
          {result.important_information.map((item) => (
            <li key={item} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 leading-relaxed">
              {item}
            </li>
          ))}
        </ul>
      ) : null}
      {result.document ? (
        <dl className="mt-5 grid gap-3 text-[var(--text-secondary)] sm:grid-cols-2">
          {result.document.document_type ? (
            <div className="rounded-2xl bg-black/20 px-4 py-3">
              <dt className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--text-primary)]">
                Document type
              </dt>
              <dd className="mt-1">{result.document.document_type}</dd>
            </div>
          ) : null}
          {result.document.action_required ? (
            <div className="rounded-2xl bg-black/20 px-4 py-3">
              <dt className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--text-primary)]">Action</dt>
              <dd className="mt-1">{result.document.action_required}</dd>
            </div>
          ) : null}
        </dl>
      ) : null}
      {result.text ? (
        <div className="mt-6 border-t border-white/10 pt-5">
          <h3 className="text-xs font-bold uppercase tracking-[0.16em] text-[var(--text-secondary)]">
            Extracted text
          </h3>
          <p className="mt-3 whitespace-pre-wrap leading-relaxed text-[var(--text-secondary)]">{result.text}</p>
        </div>
      ) : null}
    </article>
  )
}

function typeLabel(type: string): string {
  const labels: Record<string, string> = {
    document: 'Document',
    sign: 'Sign',
    currency: 'Currency',
    text: 'Text',
    table: 'Table',
    chart: 'Chart',
    screen: 'Screen',
    label: 'Label',
  }
  return labels[type] || 'Result'
}
