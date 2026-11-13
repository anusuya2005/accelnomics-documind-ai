// Small line icons drawn here, so no icon library (and no internet) is needed.
const PATHS = {
  chat: 'M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12Z',
  docs: 'M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z M14 3v5h5 M9 13h6 M9 17h6',
  file: 'M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z M14 3v5h5',
  shield: 'M12 3 5 6v5c0 4.5 3 8 7 10 4-2 7-5.5 7-10V6l-7-3Z M9 12l2 2 4-4',
  log: 'M12 7v5l3 2 M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z',
  plus: 'M12 5v14 M5 12h14',
  up: 'M12 19V5 M6 11l6-6 6 6',
  check: 'm5 12 5 5 9-10',
  copy: 'M8 8h11v11H8z M5 16V5h11',
  close: 'M6 6l12 12 M18 6 6 18',
  upload: 'M12 16V4 M7 9l5-5 5 5 M4 20h16',
  lock: 'M6 11h12v9H6z M8 11V8a4 4 0 0 1 8 0v3',
  warn: 'M12 4 3 20h18L12 4Z M12 10v4 M12 17h.01',
  search: 'M11 18a7 7 0 1 1 0-14 7 7 0 0 1 0 14Z M20 20l-4-4',
  refresh: 'M20 11a8 8 0 0 0-14.5-3.5L4 9 M4 4v5h5 M4 13a8 8 0 0 0 14.5 3.5L20 15 M20 20v-5h-5',
  right: 'm9 6 6 6-6 6',
  left: 'm15 6-6 6 6 6',
  trash: 'M4 7h16 M9 7V4h6v3 M6 7l1 13h10l1-13',
  logout: 'M10 5H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h4 M15 8l4 4-4 4 M19 12H9',
  key: 'M8 15a4 4 0 1 1 3.9-5H21v3h-2v2h-3v-2h-4.1A4 4 0 0 1 8 15Z',
  users: 'M16 20v-1a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v1 M9.5 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z M17 4.5a3.5 3.5 0 0 1 0 6.5 M21 20v-1a4 4 0 0 0-3-3.9',
  server: 'M4 5h16v6H4z M4 13h16v6H4z M8 8h.01 M8 16h.01',
} as const

export type IconName = keyof typeof PATHS

export default function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false" className="icon">
      <path d={PATHS[name]} />
    </svg>
  )
}
