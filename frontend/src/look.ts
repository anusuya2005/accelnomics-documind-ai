// Small helpers for how people and accounts look. No data leaves the browser here.

// One fixed colour per account tile, so people learn "HR is teal" without reading.
const COLORS: Record<string, string> = {
  admin: '#5b4b8a',
  hr: '#0f766e',
  it: '#1d4ed8',
  finance: '#b45309',
}

const HINTS: Record<string, string> = {
  admin: 'Manage documents, privacy checks and the audit log',
  hr: 'Leave, conduct and people policies',
  it: 'Security, passwords and incident response',
  finance: 'Lending, KYC and fee schedules',
}

export function tileColor(name: string): string {
  const key = name.trim().toLowerCase()
  if (COLORS[key]) return COLORS[key]
  let hue = 0
  for (const ch of key) hue = (hue * 31 + ch.charCodeAt(0)) % 360
  return `hsl(${hue} 45% 36%)`
}

export function tileHint(name: string): string {
  return HINTS[name.trim().toLowerCase()] ?? `Sign in to the ${name} account`
}

// "hr_anu" -> "HA", "admin1" -> "AD"
export function initials(name: string): string {
  const parts = name.replace(/\d+$/, '').split(/[^A-Za-z]+/).filter(Boolean)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[1][0]).toUpperCase()
}

// "hr_anu" -> "Anu", "admin1" -> "Admin"
export function friendlyName(username: string): string {
  const parts = username.replace(/\d+$/, '').split(/[^A-Za-z]+/).filter(Boolean)
  const word = parts.length > 1 ? parts[parts.length - 1] : (parts[0] ?? username)
  return word.charAt(0).toUpperCase() + word.slice(1)
}

// "Good morning", "Good afternoon" or "Good evening" from the computer's clock.
export function greeting(date = new Date()): string {
  const h = date.getHours()
  return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening'
}

// "hr_leave_policy.docx" -> "DOCX"
export function fileKind(name: string): string {
  const ext = name.split('.').pop() ?? ''
  return ext.length > 0 && ext.length <= 4 ? ext.toUpperCase() : 'FILE'
}

// "suspicious_text" -> "Suspicious text"
export function prettyEvent(event: string): string {
  const NAMES: Record<string, string> = { login: 'Sign-in', upload: 'Upload', suspicious_text: 'Flagged text' }
  if (NAMES[event]) return NAMES[event]
  const text = event.replace(/_/g, ' ')
  return text.charAt(0).toUpperCase() + text.slice(1)
}

// The server sends UTC times. Show them in the viewer's own time zone.
export function localTime(ts: string): string {
  const d = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(ts) ? ts : ts + 'Z')
  if (Number.isNaN(d.getTime())) return ts
  return d.toLocaleString(undefined, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}
