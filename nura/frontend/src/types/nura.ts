export type ReadMode = 'read' | 'currency' | 'sign' | 'document' | 'ask'
export type Verbosity = 'concise' | 'standard' | 'detailed'
export type TextSize = 'standard' | 'large' | 'xl'
export type ContentType =
  | 'text'
  | 'document'
  | 'sign'
  | 'currency'
  | 'chart'
  | 'table'
  | 'screen'
  | 'label'
  | 'other'

export interface CurrencyResult {
  currency: string
  denomination: number | null
  confidence: number
  spoken: string
}

export interface DocumentFields {
  document_type: string | null
  audience: string | null
  dates: string[]
  amounts: string[]
  action_required: string | null
  sections: string[]
}

export interface AnalysisResult {
  type: ContentType
  confidence: number
  text: string
  title: string | null
  important_information: string[]
  summary: string
  spoken: string
  currency: CurrencyResult | null
  document: DocumentFields | null
}

export interface AudioPayload {
  url: string | null
  mime_type: string
  base64: string | null
}

export interface ApiResponse {
  success: boolean
  type: string | null
  result: AnalysisResult | Record<string, unknown> | null
  audio: AudioPayload | null
  confidence: number | null
  spoken: string | null
  session_id: string | null
  error: string | null
}

export interface HistoryItem {
  id: string
  createdAt: number
  mode: ReadMode
  title: string
  spoken: string
  type: string
  result: AnalysisResult
  audioBase64: string | null
}

export interface NuraSettings {
  voiceId: string
  speechSpeed: number
  verbosity: Verbosity
  defaultMode: ReadMode
  autoPlay: boolean
  continuousReading: boolean
  retainImages: boolean
  textSize: TextSize
  highContrast: boolean
  reducedMotion: boolean
}
