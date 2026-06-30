/**
 * src/components/LoadingSpinner.jsx
 * ───────────────────────────────────
 * Reusable full-screen or inline loading spinner.
 *
 * Props:
 *   size    - 'sm' | 'md' | 'lg' (default: 'md')
 *   message - Optional loading text to display below the spinner
 */

const SIZE_MAP = {
  sm: 'h-6 w-6 border-2',
  md: 'h-10 w-10 border-2',
  lg: 'h-16 w-16 border-4',
};

export default function LoadingSpinner({ size = 'md', message }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12">
      <div
        className={`animate-spin rounded-full border-transparent ${SIZE_MAP[size]}`}
        style={{ borderTopColor: 'var(--color-accent-blue)' }}
        role="status"
        aria-label="Loading"
      />
      {message && (
        <p className="text-sm text-muted">{message}</p>
      )}
    </div>
  );
}
