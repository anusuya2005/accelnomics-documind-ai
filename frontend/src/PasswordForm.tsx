import { useState } from 'react'
import type { FormEvent } from 'react'
import { api, errorText, setMustChange } from './api'

const MIN_LENGTH = 10

// One small form, used in the account menu and on the first-login screen.
export default function PasswordForm({
  forced = false,
  onDone,
  onCancel,
}: {
  forced?: boolean
  onDone?: () => void
  onCancel?: () => void
}) {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [again, setAgain] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setDone(false)
    // These checks only save a round trip. The server checks everything again.
    if (next.length < MIN_LENGTH) return setError(`The new password needs at least ${MIN_LENGTH} characters.`)
    if (next !== again) return setError('The two new passwords are not the same.')
    setBusy(true)
    try {
      await api('/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({ current_password: current, new_password: next }),
      })
      setDone(true)
      if (forced) {
        setMustChange(false)
        onDone?.()
      }
      setCurrent('')
      setNext('')
      setAgain('')
    } catch (err) {
      setError(errorText(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="pwform" aria-label="Change password">
      <label>
        {forced ? 'Password you were given' : 'Current password'}
        <input type="password" value={current} onChange={(e) => setCurrent(e.target.value)} autoComplete="current-password" required autoFocus />
      </label>
      <label>
        New password
        <input type="password" value={next} onChange={(e) => setNext(e.target.value)} autoComplete="new-password" required minLength={MIN_LENGTH} />
        <span className="hint">At least {MIN_LENGTH} characters</span>
      </label>
      <label>
        Repeat new password
        <input type="password" value={again} onChange={(e) => setAgain(e.target.value)} autoComplete="new-password" required />
      </label>
      {error && <p role="alert" className="error small">{error}</p>}
      {done && !forced && <p role="status" className="ok small">Password changed. Other devices were signed out.</p>}
      <div className="row end">
        {onCancel && <button type="button" className="secondary" onClick={onCancel}>{done ? 'Close' : 'Cancel'}</button>}
        <button disabled={busy}>{busy ? 'Saving…' : 'Save password'}</button>
      </div>
    </form>
  )
}
