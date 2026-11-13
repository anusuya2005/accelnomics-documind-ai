import { useEffect, useRef, useState } from 'react'
import Icon from './Icons'
import PasswordForm from './PasswordForm'
import { initials, tileColor } from './look'

// The "who am I" chip in the header. It opens a small panel with the details and the account actions.
export default function UserMenu({
  username,
  isAdmin,
  departments,
  onSignOut,
}: {
  username: string
  isAdmin: boolean
  departments: string[]
  onSignOut: () => void
}) {
  const [open, setOpen] = useState(false)
  const [view, setView] = useState<'menu' | 'password'>('menu')
  const box = useRef<HTMLDivElement>(null)

  const role = isAdmin ? 'Administrator' : 'Staff'
  const scope = isAdmin ? 'All departments' : departments.join(', ') || 'No department yet'
  const colour = tileColor(isAdmin ? 'admin' : (departments[0] ?? username))
  // Short line under the name in the header: "HR staff" or "Administrator".
  const line = isAdmin ? 'Administrator' : departments.length > 0 ? `${departments.join(' and ')} staff` : 'Staff'

  useEffect(() => {
    if (!open) return
    const close = () => { setOpen(false); setView('menu') }
    const onDown = (e: MouseEvent) => { if (box.current && !box.current.contains(e.target as Node)) close() }
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') close() }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    <div className="usermenu" ref={box}>
      <button className="userchip" aria-haspopup="dialog" aria-expanded={open} onClick={() => { setOpen(!open); setView('menu') }}>
        <span className="avatar" style={{ background: colour }} aria-hidden="true">{initials(username)}</span>
        <span className="who">
          <span className="who-name">{username}</span>
          <span className="who-role">{line}</span>
        </span>
        <span className="caret" aria-hidden="true">▾</span>
      </button>

      {open && (
        <div className="panel" role="dialog" aria-label="Your account">
          <div className="panel-head">
            <span className="avatar lg" style={{ background: colour }} aria-hidden="true">{initials(username)}</span>
            <div>
              <strong>{username}</strong>
              <div className="muted small">Signed in</div>
            </div>
          </div>

          {view === 'menu' ? (
            <>
              <dl className="facts">
                <div><dt>Role</dt><dd>{role}</dd></div>
                <div><dt>{isAdmin ? 'Access' : 'Department'}</dt><dd>{scope}</dd></div>
              </dl>
              <div className="panel-actions">
                <button className="menu-item" onClick={() => setView('password')}><Icon name="key" size={16} /> Change password</button>
                <button className="menu-item" onClick={onSignOut}><Icon name="logout" size={16} /> Sign out</button>
              </div>
            </>
          ) : (
            <>
              <h3 className="panel-title">Change password</h3>
              <PasswordForm onCancel={() => setView('menu')} />
            </>
          )}
        </div>
      )}
    </div>
  )
}
