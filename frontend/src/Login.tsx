import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import Brand from './Brand'
import Icon from './Icons'
import { api, errorText, saveSession } from './api'
import { initials, tileColor, tileHint } from './look'
import type { LoginResult } from './types'

// Remember only the last username per tile on this computer. Never the password.
const remembered = (tile: string) => {
  try { return localStorage.getItem('lastUser:' + tile) ?? '' } catch { return '' }
}
const remember = (tile: string, name: string) => {
  try { localStorage.setItem('lastUser:' + tile, name) } catch { /* private mode: fine */ }
}

export default function Login({ onSignedIn }: { onSignedIn: () => void }) {
  const [tiles, setTiles] = useState<string[] | null>(null)
  const [tile, setTile] = useState<string | null>(null)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [show, setShow] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api<{ options: string[] }>('/login-options')
      .then((r) => setTiles(r.options))
      .catch(() => setTiles([]))          // backend not ready: show the plain form instead of tiles
  }, [])

  function choose(name: string | null) {
    setTile(name)
    setUsername(name ? remembered(name) : '')
    setPassword('')
    setShow(false)
    setError(null)
  }

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const result = await api<LoginResult>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      })
      remember(tile ?? '', username)
      saveSession(result)
      onSignedIn()
    } catch (err) {
      setError(errorText(err))
    } finally {
      setBusy(false)
    }
  }

  const showTiles = tiles !== null && tiles.length > 0 && tile === null

  return (
    <div className="login-shell">
      <aside className="login-brand">
        <div className="brand brand-light">
          <Brand size={36} />
          <span className="brand-name">Accelnomics DocuMind AI</span>
        </div>

        <div className="login-pitch">
          <h1>Ask your company documents. Get answers with their sources.</h1>

          {/* A fixed example of what an answer looks like, so a new visitor understands the product at a glance. */}
          <figure className="demo" aria-label="Example of an answer">
            <div className="demo-q">How many days of annual leave do employees get?</div>
            <div className="demo-a">
              Every permanent employee gets <strong>24 days</strong> of paid annual leave per calendar year.
              <span className="demo-cite">1</span>
            </div>
            <div className="demo-src">
              <div className="demo-file"><span className="file-badge sm" data-kind="DOCX">DOCX</span> hr_leave_policy.docx</div>
              <p className="paper-line"><mark>Every permanent employee is entitled to 24 days of paid annual leave per calendar year.</mark></p>
            </div>
          </figure>

          <ul className="trust">
            <li><Icon name="lock" size={18} /><span><strong>Private.</strong> The AI runs on this computer. Nothing goes to the internet.</span></li>
            <li><Icon name="users" size={18} /><span><strong>Separated.</strong> Each department only sees its own documents.</span></li>
          </ul>
        </div>

        <p className="login-foot">A prototype for review. Not security-certified.</p>
      </aside>

      <main className="login-main">
        <div className="login-box">
          {tiles === null && <p className="muted" role="status">Loading…</p>}

          {showTiles && (
            <>
              <div className="stack tight">
                <h2>Choose your account</h2>
                <p className="muted">Pick the one you use at work, then sign in.</p>
              </div>
              <div className="tile-list">
                {tiles.map((t) => (
                  <button key={t} className="tile" onClick={() => choose(t)}>
                    <span className="avatar lg" style={{ background: tileColor(t) }} aria-hidden="true">{initials(t)}</span>
                    <span className="tile-text">
                      <strong>{t}</strong>
                      <span className="muted small">{tileHint(t)}</span>
                    </span>
                    <span className="chev" aria-hidden="true"><Icon name="right" size={18} /></span>
                  </button>
                ))}
              </div>
            </>
          )}

          {tiles !== null && !showTiles && (
            <form onSubmit={submit} className="stack login-form">
              {tile && (
                <button type="button" className="back" onClick={() => choose(null)}><Icon name="left" size={16} /> All accounts</button>
              )}
              <div className="login-who">
                {tile && <span className="avatar lg" style={{ background: tileColor(tile) }} aria-hidden="true">{initials(tile)}</span>}
                <div>
                  <h2>{tile ? `${tile} account` : 'Sign in'}</h2>
                  <p className="muted small">{tile ? tileHint(tile) : 'Enter your username and password.'}</p>
                </div>
              </div>
              <label>
                Username
                <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required autoFocus={!username} />
              </label>
              <label>
                Password
                <span className="pw-field">
                  <input type={show ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required autoFocus={Boolean(username)} />
                  <button type="button" className="link" onClick={() => setShow(!show)} aria-pressed={show}>{show ? 'Hide' : 'Show'}</button>
                </span>
              </label>
              {error && <p role="alert" className="error">{error}</p>}
              <button className="wide" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
            </form>
          )}
        </div>
      </main>
    </div>
  )
}
