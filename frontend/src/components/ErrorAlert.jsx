/**
 * src/components/ErrorAlert.jsx
 * ──────────────────────────────
 * Reusable inline error message component.
 *
 * Props:
 *   message - Error string to display
 *   onRetry - Optional callback for a retry button
 */

export default function ErrorAlert({ message, onRetry }) {
  return (
    <div
      className="flex items-start gap-3 rounded-xl border p-4"
      style={{
        backgroundColor: 'rgba(239,68,68,0.08)',
        borderColor: 'rgba(239,68,68,0.25)',
      }}
      role="alert"
    >
      <span className="mt-0.5 text-lg">⚠️</span>
      <div className="flex-1">
        <p className="text-sm font-medium" style={{ color: 'var(--color-negative)' }}>
          {message || 'An unexpected error occurred.'}
        </p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-xs font-semibold underline transition-opacity hover:opacity-70"
          style={{ color: 'var(--color-negative)' }}
        >
          Retry
        </button>
      )}
    </div>
  );
}
