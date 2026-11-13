import { useCallback, useEffect, useRef, useState } from 'react'
import type { ChangeEvent, DragEvent } from 'react'
import { api, errorText, getRole } from './api'
import Icon from './Icons'
import { fileKind, tileColor } from './look'
import type { Department, Doc, DocStatus } from './types'

const WORKING: DocStatus[] = ['queued', 'extracting', 'embedding', 'deleting']
const LABEL: Record<DocStatus, string> = {
  queued: 'Queued',
  extracting: 'Reading the file…',
  embedding: 'Indexing…',
  indexed: 'Ready',
  failed: 'Failed',
  deleting: 'Deleting…',
}

export default function DocumentsPage() {
  const isAdmin = getRole() === 'admin' // decides what to show; the backend enforces it
  const [docs, setDocs] = useState<Doc[] | null>(null)
  const [departments, setDepartments] = useState<Department[]>([])
  const [departmentId, setDepartmentId] = useState<number | null>(null)
  const [filter, setFilter] = useState<number | 'all'>('all')
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [confirming, setConfirming] = useState<string | null>(null)
  const [effectiveDate, setEffectiveDate] = useState('') // optional: the day the document starts to apply
  const fileInput = useRef<HTMLInputElement>(null)

  const load = useCallback(async () => {
    try {
      setDocs(await api<Doc[]>('/documents'))
    } catch (err) {
      setError(errorText(err))
    }
  }, [])

  useEffect(() => {
    load()
    api<Department[]>('/departments')
      .then((list) => {
        setDepartments(list)
        setDepartmentId(list[0]?.id ?? null)
      })
      .catch((err) => setError(errorText(err)))
  }, [load])

  // While any document is still being processed, ask the backend again every 2 seconds.
  const busy = docs?.some((d) => WORKING.includes(d.status)) ?? false
  useEffect(() => {
    if (!busy) return
    const timer = setInterval(load, 2000)
    return () => clearInterval(timer)
  }, [busy, load])

  async function upload(file: File | undefined) {
    if (!file || departmentId === null) return
    const form = new FormData()
    form.append('file', file)
    form.append('department_id', String(departmentId))
    if (effectiveDate) form.append('effective_date', effectiveDate)
    setError(null)
    setUploading(true)
    try {
      await api('/documents', { method: 'POST', body: form })
      await load()
    } catch (err) {
      setError(errorText(err))
    } finally {
      setUploading(false)
      if (fileInput.current) fileInput.current.value = ''
    }
  }

  const onPick = (e: ChangeEvent<HTMLInputElement>) => upload(e.target.files?.[0])
  const onDrop = (e: DragEvent) => {
    e.preventDefault()
    setDragging(false)
    upload(e.dataTransfer.files?.[0])
  }

  async function remove(doc: Doc) {
    setConfirming(null)
    try {
      await api(`/documents/${doc.id}`, { method: 'DELETE' })
      await load()
    } catch (err) {
      setError(errorText(err))
    }
  }

  const departmentName = (id: number) => departments.find((d) => d.id === id)?.name ?? `Department ${id}`
  const all = docs ?? []
  const shown = filter === 'all' ? all : all.filter((d) => d.department_id === filter)
  const stats = [
    { label: 'Documents', value: all.length },
    { label: 'Ready to search', value: all.filter((d) => d.status === 'indexed').length },
    { label: 'Searchable pieces', value: all.reduce((n, d) => n + d.chunk_count, 0) },
    { label: 'Departments', value: new Set(all.map((d) => d.department_id)).size },
  ]

  return (
    <section className="page stack-lg">
      <p className="muted lead">The files the assistant can answer from. Each one belongs to one department, and only that department can search it.</p>
      {error && <p role="alert" className="error banner">{error}</p>}

      {docs && (
        <div className="stats">
          {stats.map((s) => (
            <div key={s.label} className="stat"><strong>{s.value}</strong><span className="muted small">{s.label}</span></div>
          ))}
        </div>
      )}

      {isAdmin && (
        <div className="card upload">
          <div className="upload-fields">
            <label>
              Department
              <select value={departmentId ?? ''} onChange={(e) => setDepartmentId(Number(e.target.value))}>
                {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </label>
            <label>
              Valid from (optional)
              <input type="date" value={effectiveDate} onChange={(e) => setEffectiveDate(e.target.value)} />
            </label>
          </div>
          <div
            className={dragging ? 'dropzone dragging' : 'dropzone'}
            onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
          >
            <span className="drop-icon"><Icon name="upload" size={22} /></span>
            <div>
              <strong>{uploading ? 'Uploading…' : 'Drop a file here'}</strong>
              <p className="muted small">PDF, DOCX or TXT. It is read and indexed on this computer.</p>
            </div>
            <button type="button" className="secondary" onClick={() => fileInput.current?.click()} disabled={uploading || departmentId === null}>Choose file</button>
            <input ref={fileInput} type="file" accept=".pdf,.docx,.txt" onChange={onPick} hidden />
          </div>
        </div>
      )}

      {docs === null && !error && <p className="muted">Loading…</p>}
      {docs?.length === 0 && (
        <div className="card empty-card">
          <Icon name="docs" size={24} />
          <strong>{isAdmin ? 'No documents yet' : 'No documents available yet'}</strong>
          <p className="muted">{isAdmin ? 'Upload a PDF, DOCX or TXT file above to get started.' : 'Ask your administrator to add documents for your department.'}</p>
        </div>
      )}

      {docs && docs.length > 0 && (
        <div className="stack">
          <div className="filters" role="group" aria-label="Filter by department">
            <button className={filter === 'all' ? 'filter active' : 'filter'} onClick={() => setFilter('all')}>All</button>
            {departments.map((d) => (
              <button key={d.id} className={filter === d.id ? 'filter active' : 'filter'} onClick={() => setFilter(d.id)}>
                <span className="dot" style={{ background: tileColor(d.name) }} />{d.name}
              </button>
            ))}
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Name</th><th>Department</th><th>Valid from</th><th>Status</th><th className="num">Pieces</th>{isAdmin && <th><span className="sr-only">Actions</span></th>}</tr>
              </thead>
              <tbody>
                {shown.map((d) => (
                  <tr key={d.id}>
                    <td><span className="name-cell"><span className="file-badge" data-kind={fileKind(d.display_name)}>{fileKind(d.display_name)}</span>{d.display_name}</span></td>
                    <td><span className="dept-cell"><span className="dot" style={{ background: tileColor(departmentName(d.department_id)) }} />{departmentName(d.department_id)}</span></td>
                    <td className="muted">{d.effective_date ?? 'Not set'}</td>
                    <td>
                      <span className={`badge ${d.status === 'indexed' ? 'good' : d.status === 'failed' ? 'bad' : 'warn'}`}>{LABEL[d.status]}</span>
                      {d.status === 'failed' && d.error_message && <div className="error small">{d.error_message}</div>}
                    </td>
                    <td className="num">{d.chunk_count}</td>
                    {isAdmin && (
                      <td className="actions-cell">
                        {confirming === d.id ? (
                          <span className="confirm">
                            <button className="danger small" onClick={() => remove(d)}>Delete for good</button>
                            <button className="secondary small" onClick={() => setConfirming(null)}>Cancel</button>
                          </span>
                        ) : (
                          <button className="ghost small" onClick={() => setConfirming(d.id)} disabled={d.status === 'deleting'} aria-label={`Delete ${d.display_name}`}>
                            <Icon name="trash" size={15} /> Delete
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  )
}
