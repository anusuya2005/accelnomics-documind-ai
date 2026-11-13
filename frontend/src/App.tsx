import { useEffect, useState } from 'react'
import AskPage from './AskPage'
import AuditPage from './AuditPage'
import Brand from './Brand'
import DocumentsPage from './DocumentsPage'
import Icon from './Icons'
import Login from './Login'
import PasswordForm from './PasswordForm'
import PrivacyPage from './PrivacyPage'
import Sidebar from './Sidebar'
import type { Page } from './Sidebar'
import UserMenu from './UserMenu'
import { api, clearSession, getMustChange, getRole, getToken, getUsername } from './api'
import { friendlyName } from './look'
import type { Department, Turn } from './types'

const TITLES: Record<Page, string> = {
  ask: 'Ask your documents',
  documents: 'Documents',
  privacy: 'Privacy console',
  audit: 'Audit log',
}

export default function App() {
  const [signedIn, setSignedIn] = useState(Boolean(getToken()))
  const [page, setPage] = useState<Page>('ask')
  const [mustChange, setMustChangeState] = useState(getMustChange())
  const [departments, setDepartments] = useState<string[]>([])
  const [turns, setTurns] = useState<Turn[]>([])

  // The departments this person belongs to (the server only returns their own; admins get all).
  useEffect(() => {
    if (!signedIn || mustChange) return
    api<Department[]>('/departments')
      .then((list) => setDepartments(list.map((d) => d.name)))
      .catch(() => setDepartments([]))
  }, [signedIn, mustChange])

  if (!signedIn) return <Login onSignedIn={() => { setPage('ask'); setTurns([]); setMustChangeState(getMustChange()); setSignedIn(true) }} />

  // The server checks the role on every request. This only decides what to SHOW.
  const isAdmin = getRole() === 'admin'
  const username = getUsername() ?? ''

  function signOut() {
    // Best effort: tell the backend to end the session, then forget it here either way.
    const token = getToken()
    if (token) fetch('/api/auth/logout', { method: 'POST', headers: { Authorization: `Bearer ${token}` } }).catch(() => {})
    clearSession()
    setDepartments([])
    setTurns([])
    setSignedIn(false)
  }

  function newChat() {
    setTurns([])
    setPage('ask')
  }

  function jump(id: number) {
    setPage('ask')
    setTimeout(() => document.getElementById(`turn-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
  }

  if (mustChange) {
    return (
      <div className="center-screen">
        <div className="center-card">
          <div className="brand"><Brand size={32} /><span className="brand-name">Accelnomics DocuMind AI</span></div>
          <h2>Welcome, {friendlyName(username)}</h2>
          <p className="muted">Before you continue, choose a password that only you know. It must be different from the one you were given.</p>
          <PasswordForm forced onDone={() => setMustChangeState(false)} />
          <button className="link" onClick={signOut}>Sign out</button>
        </div>
      </div>
    )
  }

  return (
    <div className={isAdmin ? 'app has-tabs' : 'app'}>
      <Sidebar page={page} isAdmin={isAdmin} departments={departments} turns={turns} onPage={setPage} onNewChat={newChat} onJump={jump} />
      <div className="content">
        <header className="header">
          <span className="header-mark"><Brand size={28} /></span>
          <h1 className="header-title">{TITLES[page]}</h1>
          <span className="grow" />
          {page === 'ask' && turns.length > 0 && (
            <button className="secondary small only-narrow" onClick={newChat}><Icon name="plus" size={14} /> New chat</button>
          )}
          {isAdmin ? (
            <button className="pill pill-button" onClick={() => setPage('privacy')} title="See the live privacy checks">
              <Icon name="lock" size={14} /> Runs on this computer
            </button>
          ) : (
            <span className="pill" title="The AI model and your documents stay on this computer."><Icon name="lock" size={14} /> Runs on this computer</span>
          )}
          <UserMenu username={username} isAdmin={isAdmin} departments={departments} onSignOut={signOut} />
        </header>
        <main className={page === 'ask' ? 'main main-ask' : 'main'}>
          {page === 'ask' && <AskPage name={username} isAdmin={isAdmin} departments={departments} turns={turns} setTurns={setTurns} />}
          {isAdmin && page === 'documents' && <DocumentsPage />}
          {isAdmin && page === 'privacy' && <PrivacyPage />}
          {isAdmin && page === 'audit' && <AuditPage />}
        </main>
      </div>
    </div>
  )
}
