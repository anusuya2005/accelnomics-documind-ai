import { useEffect, useState } from 'react'
import { api, errorText } from './api'
import { localTime, prettyEvent } from './look'
import type { AuditResponse } from './types'

const FRIENDLY: Record<string, string> = {
  login: 'Sign-ins',
  upload: 'Uploads',
  suspicious_text: 'Flagged text',
}
const needsAttention = (event: string) => /fail|lock|suspicious|denied/.test(event)

export default function AuditPage() {
  const [data, setData] = useState<AuditResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<string>('all')

  useEffect(() => {
    api<AuditResponse>('/admin/audit?limit=50').then(setData).catch((err) => setError(errorText(err)))
  }, [])

  if (error) return <p role="alert" className="error banner page">{error}</p>
  if (!data) return <p className="muted page">Loading…</p>

  const kinds = Object.keys(data.counts)
  const rows = filter === 'all' ? data.recent : data.recent.filter((e) => e.event === filter)

  return (
    <section className="page stack-lg">
      <p className="muted lead">Who did what, and when. It records events only. It never contains document text, questions or answers.</p>

      <div className="stats">
        {kinds.map((k) => (
          <div key={k} className={needsAttention(k) ? 'stat warn' : 'stat'}>
            <strong>{data.counts[k]}</strong><span className="muted small">{FRIENDLY[k] ?? prettyEvent(k)}</span>
          </div>
        ))}
      </div>

      <div className="stack">
        <div className="filters" role="group" aria-label="Filter by event">
          <button className={filter === 'all' ? 'filter active' : 'filter'} onClick={() => setFilter('all')}>All events</button>
          {kinds.map((k) => (
            <button key={k} className={filter === k ? 'filter active' : 'filter'} onClick={() => setFilter(k)}>{prettyEvent(k)}</button>
          ))}
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>When</th><th>User</th><th>Event</th></tr></thead>
            <tbody>
              {rows.map((ev, i) => (
                <tr key={i}>
                  <td className="muted" title={`${ev.ts} UTC`}>{localTime(ev.ts)}</td>
                  <td>{ev.username ?? 'Not signed in'}</td>
                  <td><span className={needsAttention(ev.event) ? 'badge warn' : 'badge none'}>{prettyEvent(ev.event)}</span></td>
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={3} className="muted">No events of this kind yet.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}
