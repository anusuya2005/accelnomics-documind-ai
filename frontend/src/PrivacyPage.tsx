import { useCallback, useEffect, useState } from 'react'
import { api, errorText } from './api'
import Icon from './Icons'
import type { PrivacyStatus } from './types'

export default function PrivacyPage() {
  const [info, setInfo] = useState<PrivacyStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [checkedAt, setCheckedAt] = useState<Date | null>(null)
  const [running, setRunning] = useState(false)

  const run = useCallback(async () => {
    setRunning(true)
    setError(null)
    try {
      setInfo(await api<PrivacyStatus>('/privacy/status'))
      setCheckedAt(new Date())
    } catch (err) {
      setError(errorText(err))
    } finally {
      setRunning(false)
    }
  }, [])

  useEffect(() => { run() }, [run])

  if (error) return <p role="alert" className="error banner page">{error}</p>
  if (!info) return <p className="muted page">Loading…</p>

  const failed = info.checks.filter((c) => c.status !== 'pass').length
  const documents = Object.entries(info.storage.documents_by_status).map(([k, v]) => `${v} ${k}`).join(', ') || 'No documents yet'

  return (
    <section className="page stack-lg">
      <div className={failed === 0 ? 'summary good' : 'summary bad'} role="status">
        <span className="summary-icon"><Icon name={failed === 0 ? 'shield' : 'warn'} size={26} /></span>
        <div className="grow">
          <h2>{failed === 0 ? `All ${info.checks.length} checks passed` : `${failed} of ${info.checks.length} checks failed`}</h2>
          <p>
            These checks run now, on this computer, every time you open this page.
            {checkedAt && <> Last run at {checkedAt.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' })}.</>}
          </p>
        </div>
        <button className="secondary" onClick={run} disabled={running}><Icon name="refresh" size={16} /> {running ? 'Checking…' : 'Run again'}</button>
      </div>

      <ul className="checks">
        {info.checks.map((c) => (
          <li key={c.id} className="card check">
            {/* The mark and the word say pass or fail, so colour is never the only signal. */}
            <span className={`check-mark ${c.status === 'pass' ? 'good' : 'bad'}`}><Icon name={c.status === 'pass' ? 'check' : 'close'} size={16} /></span>
            <div>
              <strong>{c.title}</strong>
              <p className="muted small">{c.detail}</p>
            </div>
            <span className={`badge ${c.status === 'pass' ? 'good' : 'bad'}`}>{c.status === 'pass' ? 'Pass' : 'Fail'}</span>
          </li>
        ))}
      </ul>

      <div className="grid-2">
        <div className="card info-card">
          <h3>Models on this computer</h3>
          <dl className="kv">
            <div><dt>Writes the answers</dt><dd><code>{info.models.chat}</code></dd></div>
            <div><dt>Finds the right passages</dt><dd><code>{info.models.embedding}</code></dd></div>
          </dl>
        </div>
        <div className="card info-card">
          <h3>What is stored</h3>
          <dl className="kv">
            <div><dt>Documents</dt><dd>{documents}</dd></div>
            <div><dt>Searchable pieces</dt><dd>{info.storage.indexed_chunks}</dd></div>
            {info.storage.data_folder && <div><dt>Data folder</dt><dd><code>{info.storage.data_folder}</code> ({info.storage.uploads_size_mb} MB)</dd></div>}
          </dl>
        </div>
        <div className="card info-card">
          <h3>What stays on this computer</h3>
          <ul className="ticks">{info.what_stays_local.map((t) => <li key={t}><Icon name="check" size={15} />{t}</li>)}</ul>
        </div>
        <div className="card info-card">
          <h3>What is logged</h3>
          <ul className="ticks">{info.what_is_logged.map((t) => <li key={t}><Icon name="log" size={15} />{t}</li>)}</ul>
        </div>
      </div>

      <div className="card info-card limits">
        <h3>Known limits</h3>
        <ul className="ticks">{info.limits.map((t) => <li key={t}><Icon name="warn" size={15} />{t}</li>)}</ul>
      </div>

      <div className="card try">
        <Icon name="lock" size={20} />
        <div>
          <strong>Try it yourself</strong>
          <p className="muted small">Turn off the internet on this computer and ask a question. It still answers, because nothing leaves this computer.</p>
        </div>
      </div>
    </section>
  )
}
