import Icon from './Icons'
import { fileKind } from './look'
import type { Citation } from './types'

// The words of the answer that cite this source, used to find the closest sentence in the source text.
function words(text: string): Set<string> {
  const found = text.toLowerCase().match(/[a-z]{4,}|\d+/g) ?? []
  return new Set(found)
}

// Split the source text into sentences and mark the ones that share the most words with the answer.
// This is only a reading aid: the whole passage is always shown.
export function highlight(excerpt: string, answer: string, label: string): { text: string; mark: boolean }[] {
  const cited = answer.split('\n').filter((l) => l.includes(`[${label}]`)).join(' ') || answer
  const wanted = words(cited.replace(/\[S\d+\]/g, ' '))
  const sentences = excerpt.match(/[^.!?\n]+[.!?]*\s*/g) ?? [excerpt]
  const scores = sentences.map((s) => {
    let n = 0
    for (const w of words(s)) if (wanted.has(w)) n++
    return n
  })
  const best = Math.max(0, ...scores)
  const cut = Math.max(2, Math.ceil(best * 0.6))
  return sentences.map((text, i) => ({ text, mark: best >= 2 && scores[i] >= cut }))
}

// The signature element: the source shown like a page of the document, with the matching sentence highlighted.
export default function SourcePage({ citation, answer }: { citation: Citation; answer: string }) {
  const parts = highlight(citation.excerpt, answer, citation.label)
  const percent = Math.max(0, Math.min(100, Math.round(citation.similarity * 100)))
  return (
    <article className="source" aria-label={`Source ${citation.label}`}>
      <header className="source-head">
        <span className="file-badge" data-kind={fileKind(citation.document)}>{fileKind(citation.document)}</span>
        <div className="source-title">
          <strong>{citation.document}</strong>
          <span className="muted small">{citation.location}</span>
        </div>
        <span className="source-label">{citation.label}</span>
      </header>
      <dl className="source-meta">
        {citation.effective_date && (
          <div><dt>Valid from</dt><dd>{citation.effective_date}</dd></div>
        )}
        <div>
          <dt>Match</dt>
          <dd>
            <span className="meter" role="img" aria-label={`${percent} percent match`}><span style={{ width: `${percent}%` }} /></span>
            {percent}%
          </dd>
        </div>
      </dl>
      <div className="paper">
        <p>
          {parts.map((p, i) => (p.mark ? <mark key={i}>{p.text}</mark> : <span key={i}>{p.text}</span>))}
        </p>
      </div>
      <p className="source-note"><Icon name="check" size={14} /> Highlighted: the sentences that match the answer.</p>
    </article>
  )
}
