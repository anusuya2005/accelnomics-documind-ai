import type { LoginResult } from './types'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

// localStorage: the sign-in survives closing the window, so staff sign in once per working day.
// The server ends the session after 8 hours. The role and name are stored only to decide what to SHOW.
// The backend checks the token and the role again on every single request.
export const getToken = () => localStorage.getItem('token')
export const getRole = () => localStorage.getItem('role')
export const getUsername = () => localStorage.getItem('username')

// "must change password" is only a hint for what to SHOW. The server blocks everything else until it is done.
export const getMustChange = () => localStorage.getItem('mustChange') === '1'
export const setMustChange = (value: boolean) =>
  value ? localStorage.setItem('mustChange', '1') : localStorage.removeItem('mustChange')

export function saveSession(result: LoginResult) {
  setMustChange(Boolean(result.must_change_password))
  localStorage.setItem('token', result.token)
  localStorage.setItem('role', result.role)
  localStorage.setItem('username', result.username)
}

export function clearSession() {
  localStorage.removeItem('mustChange')
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  localStorage.removeItem('username')
}

// Staff see plain words. The technical hint (is Ollama running?) is kept for the admin only.
function friendly(status: number, serverText: string | null): string {
  const admin = getRole() === 'admin'
  if (status === 0) {
    return admin ? 'Cannot reach the server. Is the backend running?' : 'Cannot reach the server. Check your connection and try again.'
  }
  if (status === 503) {
    return admin ? (serverText ?? 'The model is not available.') : 'The assistant is busy or not available right now. Please try again in a minute.'
  }
  if (status >= 500) return 'Something went wrong on our side. Please try again.'
  return serverText ?? 'Something went wrong.'
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')

  let response: Response
  try {
    response = await fetch(`/api${path}`, { ...options, headers })
  } catch {
    throw new ApiError(0, friendly(0, null))
  }
  if (response.status === 401 && path !== '/auth/login') {
    clearSession() // the session ended: go back to the sign-in screen
    window.location.reload()
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const detail = typeof body.detail === 'string' ? body.detail : null
    if (response.status === 403 && detail === 'password_change_required') {
      setMustChange(true)          // the server says this person must choose a new password first
      window.location.reload()
    }
    throw new ApiError(response.status, friendly(response.status, body.error ?? detail))
  }
  return response.status === 204 ? (undefined as T) : response.json()
}

export const errorText = (err: unknown) => (err instanceof ApiError ? err.message : 'Unexpected error.')
