import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { ErrorState } from '../components/ErrorState'
import { PermissionPrompt } from '../components/PermissionPrompt'
import { ResultCard } from '../components/ResultCard'
import { AudioPlayer } from '../components/AudioPlayer'
import type { AnalysisResult } from '../types/nura'

const sample: AnalysisResult = {
  type: 'document',
  confidence: 0.94,
  text: 'Admission confirmed. Reporting date: 14 September 2026.',
  title: 'University Admission Letter',
  important_information: ['Admission confirmed', 'Reporting date: 14 September 2026'],
  summary: 'This is a university admission letter.',
  spoken: 'This appears to be a university admission letter.',
  currency: null,
  document: {
    document_type: 'Admission letter',
    audience: 'Applicant',
    dates: ['14 September 2026'],
    amounts: [],
    action_required: 'Report on 14 September 2026',
    sections: ['Admission', 'Programme'],
  },
}

describe('result rendering', () => {
  it('shows document title and important information', () => {
    render(<ResultCard result={sample} />)
    expect(screen.getByText('University Admission Letter')).toBeInTheDocument()
    expect(screen.getByText('Reporting date: 14 September 2026')).toBeInTheDocument()
    expect(screen.getByText(/high confidence/i)).toBeInTheDocument()
  })
})

describe('error states', () => {
  it('renders a user-facing error without technical jargon', () => {
    render(
      <ErrorState
        message="I couldn't read this clearly. Try moving closer or improving the lighting."
        actionLabel="Try again"
        onAction={() => undefined}
      />,
    )
    expect(screen.getByRole('alert')).toHaveTextContent('moving closer')
    expect(screen.queryByText(/axios/i)).not.toBeInTheDocument()
  })
})

describe('camera permission', () => {
  it('prompts the user to enable the camera', () => {
    const onRequest = vi.fn()
    render(
      <PermissionPrompt
        message="Camera access is required to read visual information."
        onRequest={onRequest}
      />,
    )
    expect(screen.getByText(/camera access is required/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /enable camera/i })).toBeInTheDocument()
  })
})

describe('audio playback', () => {
  it('exposes play, pause, repeat and stop controls', () => {
    render(
      <MemoryRouter>
        <AudioPlayer src="data:audio/mpeg;base64,AAA" autoPlay={false} speed={1} />
      </MemoryRouter>,
    )
    expect(screen.getByRole('button', { name: /play spoken result/i })).toBeEnabled()
    expect(screen.getByRole('button', { name: /repeat spoken result/i })).toBeEnabled()
    expect(screen.getByRole('button', { name: /stop spoken result/i })).toBeEnabled()
  })
})
