import type { AnalysisResult, ApiResponse, ReadMode, Verbosity } from '../types/nura'

const USER_ERRORS: Record<string, string> = {
  failed: "Nura couldn't connect to the AI service. Please check your connection.",
  network: "Nura couldn't connect to the AI service. Please check your connection.",
}

export function apiBase(): string {
  const configured = import.meta.env.VITE_API_URL
  if (configured) return configured.replace(/\/$/, '')
  return ''
}

function friendlyError(status: number, fallback?: string): string {
  if (fallback) return fallback
  if (status === 413) return 'That file is too large. Try capturing again from a bit farther away.'
  if (status === 429) return 'Nura is busy right now. Please wait a moment and try again.'
  if (status >= 500) return "Nura couldn't connect to the AI service. Please check your connection."
  return "I couldn't read this clearly. Try moving closer or improving the lighting."
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function parseResponse(response: Response): Promise<ApiResponse> {
  let body: ApiResponse
  try {
    body = (await response.json()) as ApiResponse
  } catch {
    throw new ApiError(friendlyError(response.status), response.status)
  }
  if (!response.ok || body.success === false) {
    throw new ApiError(friendlyError(response.status, body.error ?? undefined), response.status)
  }
  return body
}

export async function analyzeImage(options: {
  blob: Blob
  mode: ReadMode
  verbosity: Verbosity
  speed: number
  speak: boolean
  sessionId: string
  signal?: AbortSignal
}): Promise<ApiResponse> {
  const form = new FormData()
  form.append('image', options.blob, 'capture.jpg')
  form.append('mode', options.mode)
  form.append('verbosity', options.verbosity)
  form.append('speak', String(options.speak))
  form.append('speed', String(options.speed))

  const path = options.mode === 'read' ? '/api/read' : `/api/${options.mode}`
  try {
    const response = await fetch(`${apiBase()}${path}`, {
      method: 'POST',
      body: form,
      headers: { 'X-Nura-Session': options.sessionId },
      signal: options.signal,
    })
    return await parseResponse(response)
  } catch (error) {
    if (error instanceof ApiError) throw error
    if ((error as Error).name === 'AbortError') throw error
    throw new ApiError(USER_ERRORS.network, 0)
  }
}

export async function askQuestion(options: {
  question?: string
  audio?: Blob
  verbosity: Verbosity
  speed: number
  speak: boolean
  sessionId: string
  signal?: AbortSignal
}): Promise<ApiResponse> {
  const form = new FormData()
  if (options.question) form.append('question', options.question)
  if (options.audio) form.append('audio', options.audio, 'ask.webm')
  form.append('verbosity', options.verbosity)
  form.append('speak', String(options.speak))
  form.append('speed', String(options.speed))
  try {
    const response = await fetch(`${apiBase()}/api/ask`, {
      method: 'POST',
      body: form,
      headers: { 'X-Nura-Session': options.sessionId },
      signal: options.signal,
    })
    return await parseResponse(response)
  } catch (error) {
    if (error instanceof ApiError) throw error
    if ((error as Error).name === 'AbortError') throw error
    throw new ApiError(USER_ERRORS.network, 0)
  }
}

export async function synthesizeSpeech(text: string, speed: number): Promise<Blob> {
  const response = await fetch(`${apiBase()}/api/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, speed }),
  })
  if (!response.ok) {
    throw new ApiError(
      'The spoken response isn\'t available right now. The text result is still ready.',
      response.status,
    )
  }
  return await response.blob()
}

export async function transcribeAudio(audio: Blob, sessionId: string): Promise<string> {
  const form = new FormData()
  form.append('audio', audio, 'speech.webm')
  const response = await fetch(`${apiBase()}/api/stt`, {
    method: 'POST',
    body: form,
    headers: { 'X-Nura-Session': sessionId },
  })
  const body = await parseResponse(response)
  const result = body.result as { text?: string } | null
  return result?.text || body.spoken || ''
}

export async function clearRemoteSession(sessionId: string): Promise<void> {
  const form = new FormData()
  form.append('session_id', sessionId)
  await fetch(`${apiBase()}/api/session/clear`, { method: 'POST', body: form })
}

export function isAnalysisResult(value: unknown): value is AnalysisResult {
  return Boolean(value && typeof value === 'object' && 'spoken' in (value as object) && 'type' in (value as object))
}
