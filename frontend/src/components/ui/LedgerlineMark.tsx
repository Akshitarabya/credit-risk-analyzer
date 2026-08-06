interface LedgerlineMarkProps {
  className?: string;
}

/**
 * The product's signature visual: a horizontal line with a marker sitting
 * along it, representing an applicant's position on the risk continuum
 * (low → high). It's a literal depiction of what the product does, reused
 * as the wordmark's icon, the auth page hero, and later as the base shape
 * for the actual risk gauge on the decision page.
 */
export default function LedgerlineMark({ className = "" }: LedgerlineMarkProps) {
  return (
    <svg
      viewBox="0 0 120 24"
      className={className}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <line x1="2" y1="12" x2="118" y2="12" stroke="currentColor" strokeOpacity="0.25" strokeWidth="2" />
      <circle cx="34" cy="12" r="4" fill="currentColor" />
      <circle cx="86" cy="12" r="4" fill="currentColor" fillOpacity="0.35" />
    </svg>
  );
}
