import { useEffect, useRef, useState } from 'react'
import type { Dispatch, FormEvent, SetStateAction } from 'react'
import { api, errorText } from './api'
import Icon from './Icons'
import { fileKind, friendlyName, greeting, tileColor } from './look'
import SourcePage from './SourcePage'
import type { AskResponse, Citation, Turn } from './types'

// Starter questions per department. Change these to questions your own documents answer.
const SUGGESTIONS: Record<string, string[]> = {
  HR: ['How many days of annual leave do employees get?', 'How many unused leave days can be carried forward?'],
  IT: ['What is the password policy?', 'What should I do if I find a security incident?'],
  Finance: ['What is the loan approval policy?', 'What changed in the 2025 fee schedule?'],
}

function suggestionsFor(departments: string[], isAdmin: boolean): { dept: string; q: string }[] {
  const names = isAdmin ? Object.keys(SUGGESTIONS) : departments
  const out: { dept: string; q: string }[] = []
  for (const d of names) for (const q of (SUGGESTIONS[d] ?? []).slice(0, isAdmin ? 1 : 2)) out.push({ dept: d, q })
  return out.slice(0, 4)
}

const STATUS: Record<AskResponse['status'], { text: string; hint: string; className: string }> = {
  supported: { text: 'Answered from your documents', hint: '', className: 'badge good' },
  limited: {
    text: 'Check the sources',
    hint: 'Part of this answer could not be fully matched to the documents. Read the sources before you rely on it.',
    className: 'badge warn',
  },
  no_evidence: {
    text: 'Not found in your documents',
    hint: 'None of the documents you can open answer this question, so nothing was guessed.',
    className: 'badge none',
  },
}

// Shows plain text only (React escapes it), turning "- item" lines into a list and [S1] into a button that opens the source.
function AnswerText({ text, onCite }: { text: string; onCite: (label: string) => void }) {
  const blocks: { list: boolean; lines: string[] }[] = []
  for (const line of text.split('\n')) {
    if (!line.trim()) continue
    const m = line.match(/^\s*(?:[-*•]|\d+[.)])\s+(.*)$/)
    const last = blocks[blocks.length - 1]
    if (m) {
      if (last?.list) last.lines.push(m[1])
      else blocks.push({ list: true, lines: [m[1]] })
    } else {
      blocks.push({ list: false, lines: [line.trim()] })
    }
  }
  const inline = (s: string) =>
    s.split(/(\[S\d+\])/).map((part, i) => {
      if (!/^\[S\d+\]$/.test(part)) return <span key={i}>{part}</span>
      const label = part.slice(1, -1)
      return <button key={i} type="button" className="cite" onClick={() => onCite(label)} title={`Show source ${label}`}>{label.slice(1)}</button>
    })
  return (
    <div className="answer">
      {blocks.map((b, i) =>
        b.list ? (
          <ul key={i}>{b.lines.map((l, j) => <li key={j}>{inline(l)}</li>)}</ul>
        ) : (
          <p key={i}>{inline(b.lines[0])}</p>
        ),
      )}
    </div>
  )
}

function Waiting({ since }: { since: number }) {
  const [now, setNow] = useState(Date.now())
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [])
  const seconds = Math.max(0, Math.floor((now - since) / 1000))
  return (
    <div className="bubble reply waiting" role="status">
      <span className="dots" aria-hidden="true"><i /><i /><i /></span>
      <span>{seconds < 4 ? 'Searching your documents' : 'Writing the answer from the matching passages'}</span>
      <span className="muted">{seconds}s</span>
    </div>
  )
}

function Reply({
  turn,
  active,
  onCite,
}: {
  turn: Turn
  active: Citation | undefined
  onCite: (label: string) => void
}) {
  const result = turn.result as AskResponse
  const [copied, setCopied] = useState(false)

  async function copy() {
    try {
      await navigator.clipboard.writeText(result.answer)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch { /* clipboard blocked: nothing to do */ }
  }

  return (
    <div className="bubble reply stack">
      <div className="reply-top">
        <span className={STATUS[result.status].className}>
          <Icon name={result.status === 'supported' ? 'check' : result.status === 'limited' ? 'warn' : 'search'} size={13} /> {STATUS[result.status].text}
        </span>
        {turn.ms !== undefined && <span className="muted small">Answered in {Math.max(1, Math.round(turn.ms / 1000))} s</span>}
      </div>
      {STATUS[result.status].hint && <p className="muted small">{STATUS[result.status].hint}</p>}
      <AnswerText text={result.answer} onCite={onCite} />
      {result.warnings?.map((w) => <p key={w} className="notice">{w}</p>)}
      {result.unsupported_numbers && result.unsupported_numbers.length > 0 && (
        <p className="notice">These numbers could not be found in the cited text: {result.unsupported_numbers.join(', ')}.</p>
      )}
      {result.citations.length > 0 && (
        <div className="reply-sources">
          <span className="muted small">Sources</span>
          <div className="chips">
            {result.citations.map((c) => (
              <button key={c.label} className={active?.label === c.label ? 'chip active' : 'chip'} aria-pressed={active?.label === c.label} onClick={() => onCite(c.label)}>
                <span className="file-badge sm" data-kind={fileKind(c.document)}>{fileKind(c.document)}</span>
                {c.document}
              </button>
            ))}
          </div>
        </div>
      )}
      {active && <div className="source-inline"><SourcePage citation={active} answer={result.answer} /></div>}
      <div className="reply-actions">
        <button className="ghost small" onClick={copy}><Icon name={copied ? 'check' : 'copy'} size={14} /> {copied ? 'Copied' : 'Copy answer'}</button>
      </div>
    </div>
  )
}

export default function AskPage({
  name,
  isAdmin,
  departments,
  turns,
  setTurns,
}: {
  name: string
  isAdmin: boolean
  departments: string[]
  turns: Turn[]
  setTurns: Dispatch<SetStateAction<Turn[]>>
}) {
  const suggestions = suggestionsFor(departments, isAdmin)
  const [question, setQuestion] = useState('')
  const [picked, setPicked] = useState<{ id: number; label: string } | null>(null)
  const bottom = useRef<HTMLDivElement>(null)
  const loading = turns.some((t) => !t.result && !t.error)

  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [turns.length, loading])

  // The source on show: the one the person picked, otherwise the first source of the newest answer.
  const latest = turns[turns.length - 1]
  const shownTurn = (picked && turns.find((t) => t.id === picked.id)) || latest
  const shownCitation: Citation | undefined = shownTurn?.result?.citations.find((c) => (picked && shownTurn.id === picked.id ? c.label === picked.label : false))
    ?? shownTurn?.result?.citations[0]

  async function ask(text: string) {
    const q = text.trim()
    if (q.length < 3 || loading) return
    const id = Date.now()
    setPicked(null)
    setTurns((t) => [...t, { id, question: q }])
    setQuestion('')
    try {
      const result = await api<AskResponse>('/ask', { method: 'POST', body: JSON.stringify({ question: q }) })
      setTurns((t) => t.map((x) => (x.id === id ? { ...x, result, ms: Date.now() - id } : x)))
    } catch (err) {
      setTurns((t) => t.map((x) => (x.id === id ? { ...x, error: errorText(err) } : x)))
    }
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    ask(question)
  }

  const hasPanelContent = shownTurn && shownTurn.result
  return (
    <section className="ask">
      <div className="ask-main">
        <div className="thread">
          <div className="thread-inner">
            {turns.length === 0 && (
              <div className="welcome">
                <h2>{greeting()}, {friendlyName(name)}.</h2>
                <p className="muted">Ask a question in your own words. The answer comes only from documents you are allowed to open, and the source sits right next to it.</p>
                {suggestions.length > 0 && (
                  <div className="suggest">
                    {suggestions.map((s) => (
                      <button key={s.q} className="suggest-card" onClick={() => ask(s.q)}>
                        <span className="suggest-dept"><span className="dot" style={{ background: tileColor(s.dept) }} />{s.dept}</span>
                        <span>{s.q}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
            {turns.map((t) => (
              <div key={t.id} id={`turn-${t.id}`} className="turn">
                <div className="bubble me">{t.question}</div>
                {t.error && <p role="alert" className="error bubble reply">{t.error}</p>}
                {t.result && (
                  <Reply
                    turn={t}
                    active={shownTurn?.id === t.id ? shownCitation : undefined}
                    onCite={(label) => setPicked({ id: t.id, label })}
                  />
                )}
                {!t.result && !t.error && <Waiting since={t.id} />}
              </div>
            ))}
            <div ref={bottom} />
          </div>
        </div>

        <form onSubmit={submit} className="composer">
          <div className="composer-box">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask about a policy, a number or a procedure"
              maxLength={2000}
              aria-label="Your question"
              autoFocus
            />
            <button className="send" disabled={loading || question.trim().length < 3} aria-label="Ask">
              <Icon name="up" size={18} />
            </button>
          </div>
          <p className="fineprint">Answers come only from your documents. Check the source before you rely on a number.</p>
        </form>
      </div>

      <aside className="evidence" aria-label="Source">
        {shownCitation && shownTurn?.result ? (
          <>
            <h2 className="evidence-title">Source</h2>
            <SourcePage citation={shownCitation} answer={shownTurn.result.answer} />
            {shownTurn.result.citations.length > 1 && (
              <p className="muted small">This answer uses {shownTurn.result.citations.length} sources. Pick another below the answer.</p>
            )}
          </>
        ) : (
          <div className="evidence-empty">
            <span className="evidence-icon"><Icon name="file" size={22} /></span>
            <h2>{hasPanelContent ? 'No source for this answer' : 'Sources appear here'}</h2>
            <p className="muted">
              {hasPanelContent
                ? 'Nothing in your documents matched this question, so nothing was guessed.'
                : 'Every answer shows the document page it came from, with the matching sentence highlighted.'}
            </p>
          </div>
        )}
      </aside>
    </section>
  )
}
