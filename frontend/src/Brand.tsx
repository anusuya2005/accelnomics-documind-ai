// The logo mark: a document with a check, drawn here so no image file is needed.
export default function Brand({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" role="img" aria-label="Accelnomics DocuMind AI" className="brand-mark">
      <rect width="32" height="32" rx="8" fill="currentColor" />
      <path d="M10 7.5h8l5 5V24a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 9 24V9a1.5 1.5 0 0 1 1-1.5Z" fill="none" stroke="#fff" strokeWidth="1.6" strokeLinejoin="round" />
      <path d="M18 7.5V13h5" fill="none" stroke="#fff" strokeWidth="1.6" strokeLinejoin="round" />
      <path d="m12.8 18.6 2.2 2.2 4.4-4.6" fill="none" stroke="#f2b84b" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
