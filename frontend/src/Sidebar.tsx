import Brand from './Brand'
import Icon from './Icons'
import type { IconName } from './Icons'
import { tileColor } from './look'
import type { Turn } from './types'

export type Page = 'ask' | 'documents' | 'privacy' | 'audit'

const NAV: { id: Page; label: string; icon: IconName; admin: boolean }[] = [
  { id: 'ask', label: 'Ask', icon: 'chat', admin: false },
  { id: 'documents', label: 'Documents', icon: 'docs', admin: true },
  { id: 'privacy', label: 'Privacy', icon: 'shield', admin: true },
  { id: 'audit', label: 'Audit log', icon: 'log', admin: true },
]

export default function Sidebar({
  page,
  isAdmin,
  departments,
  turns,
  onPage,
  onNewChat,
  onJump,
}: {
  page: Page
  isAdmin: boolean
  departments: string[]
  turns: Turn[]
  onPage: (p: Page) => void
  onNewChat: () => void
  onJump: (id: number) => void
}) {
  const items = NAV.filter((n) => !n.admin || isAdmin)
  return (
    <aside className="sidebar">
      <div className="side-brand">
        <Brand size={32} />
        <span className="brand-name">Accelnomics<br />DocuMind AI</span>
      </div>

      <button className="side-new" onClick={onNewChat}><Icon name="plus" size={16} /> New chat</button>

      <nav aria-label="Main" className="side-nav">
        {items.map((n) => (
          <button key={n.id} className={page === n.id ? 'side-link active' : 'side-link'} aria-current={page === n.id ? 'page' : undefined} onClick={() => onPage(n.id)}>
            <Icon name={n.icon} /> <span>{n.label}</span>
          </button>
        ))}
      </nav>

      {turns.length > 0 && (
        <div className="side-recent">
          <h2 className="side-heading">This session</h2>
          <ul>
            {turns.slice().reverse().slice(0, 8).map((t) => (
              <li key={t.id}><button className="side-recent-item" title={t.question} onClick={() => onJump(t.id)}>{t.question}</button></li>
            ))}
          </ul>
        </div>
      )}

      <div className="side-foot">
        <div className="side-access">
          <h2 className="side-heading">Your access</h2>
          {isAdmin ? (
            <p className="side-dept"><span className="dot" style={{ background: tileColor('admin') }} />All departments</p>
          ) : departments.length > 0 ? (
            departments.map((d) => <p key={d} className="side-dept"><span className="dot" style={{ background: tileColor(d) }} />{d}</p>)
          ) : (
            <p className="side-dept">No department yet</p>
          )}
        </div>
        <p className="side-note">A prototype for review. Not security-certified.</p>
      </div>
    </aside>
  )
}
