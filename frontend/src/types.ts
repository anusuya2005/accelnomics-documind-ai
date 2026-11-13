export type AnswerStatus = 'supported' | 'limited' | 'no_evidence'

export interface Citation {
  label: string
  document_id: string
  document: string
  location: string
  excerpt: string
  similarity: number
  effective_date?: string | null
}

export interface AskResponse {
  status: AnswerStatus
  answer: string
  citations: Citation[]
  unsupported_numbers?: string[]
  warnings?: string[]
  scope?: { departments: string[]; model: string }
}

export type DocStatus = 'queued' | 'extracting' | 'embedding' | 'indexed' | 'failed' | 'deleting'

export interface Doc {
  id: string
  display_name: string
  department_id: number
  status: DocStatus
  error_message: string | null
  chunk_count: number
  effective_date: string | null
}

export interface Department {
  id: number
  name: string
}

export interface Check {
  id: string
  title: string
  status: 'pass' | 'fail'
  detail: string
}

export interface PrivacyStatus {
  checks: Check[]
  models: { chat: string; embedding: string; installed: string[] }
  storage: {
    documents_by_status: Record<string, number>
    indexed_chunks: number
    data_folder?: string
    uploads_size_mb?: number
  }
  what_stays_local: string[]
  what_is_logged: string[]
  limits: string[]
}

export interface AuditEvent {
  ts: string
  username: string | null
  event: string
  detail: string | null
}

export interface AuditResponse {
  counts: Record<string, number>
  recent: AuditEvent[]
}

export interface LoginResult {
  token: string
  role: 'admin' | 'staff'
  username: string
  must_change_password?: boolean
}

// One question and its answer in the current chat (kept in the browser only, never saved).
export interface Turn {
  id: number
  question: string
  result?: AskResponse
  error?: string
  ms?: number // how long the answer took
}
