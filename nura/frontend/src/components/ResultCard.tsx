import type { AnalysisResult } from '../types/nura'
import { ConfidenceIndicator } from './ConfidenceIndicator'

export function ResultCard({ result }: { result: AnalysisResult }) {
  const heading = result.title || typeLabel(result.type)
  return (
    <article className="rounded-[1.75rem] border border-[var(--border)] bg-[var(--surface)] p-5">
      <p className="text-xs font-bold uppercase tracking-[0.18em] text-[var(--accent)]">
        {typeLabel(result.type)}
      </p>
      <h2 className="mt-2 font-display text-2xl font-semibold">{heading}</h2>
      <div className="mt-2">
        <ConfidenceIndicator value={result.confidence} />
      </div>
      {result.summary ? (
        <p className="mt-4 text-lg leading-relaxed">{result.summary}</p>
      ) : null}
      {result.important_information.length > 0 ? (
        <ul className="mt-4 space-y-2">
          {result.important_information.map((item) => (
            <li key={item} className="rounded-2xl bg-[var(--surface-elevated)] px-4 py-3">
              {item}
            </li>
          ))}
        </ul>
      ) : null}
      {result.document ? (
        <dl className="mt-4 space-y-2 text-[var(--text-secondary)]">
          {result.document.document_type ? (
            <div>
              <dt className="text-sm font-bold text-[var(--text-primary)]">Document type</dt>
              <dd>{result.document.document_type}</dd>
            </div>
          ) : null}
          {result.document.action_required ? (
            <div>
              <dt className="text-sm font-bold text-[var(--text-primary)]">Action</dt>
              <dd>{result.document.action_required}</dd>
            </div>
          ) : null}
        </dl>
      ) : null}
      {result.text ? (
        <div className="mt-5 border-t border-[var(--border)] pt-4">
          <h3 className="text-sm font-bold uppercase tracking-[0.16em] text-[var(--text-secondary)]">
            Extracted text
          </h3>
          <p className="mt-2 whitespace-pre-wrap leading-relaxed text-[var(--text-secondary)]">
            {result.text}
          </p>
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
