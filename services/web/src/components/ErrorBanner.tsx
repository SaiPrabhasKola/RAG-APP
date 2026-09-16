import type { UiError } from "../api/types";

interface ErrorBannerProps {
  error: UiError;
  onDismiss?: () => void;
}

function statusLabel(status: number): string | null {
  if (status === 0) {
    return "connection refused — is the service running?";
  }

  if (status > 0) {
    return `HTTP ${status}`;
  }

  return null;
}

export function ErrorBanner({ error, onDismiss }: ErrorBannerProps) {
  const label = statusLabel(error.status);

  return (
    <div
      role="alert"
      aria-live="assertive"
      className="flex items-start gap-3 rounded-lg border border-rose-200 bg-rose-50 px-3.5 py-3 text-sm text-rose-800"
    >
      <svg
        className="mt-0.5 size-4 shrink-0"
        viewBox="0 0 20 20"
        fill="currentColor"
        aria-hidden="true"
      >
        <path
          fillRule="evenodd"
          d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm-1-5a1 1 0 1 1 2 0 1 1 0 0 1-2 0Zm.25-8a.75.75 0 0 0-1.5 0v4a.75.75 0 0 0 1.5 0V5Z"
          clipRule="evenodd"
        />
      </svg>

      <div className="flex-1">
        <p className="font-medium">{error.message}</p>
        {label ? <p className="mt-0.5 text-xs text-rose-600">{label}</p> : null}
      </div>

      {onDismiss ? (
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Dismiss error"
          className="rounded p-1 text-rose-500 transition hover:bg-rose-100 hover:text-rose-700"
        >
          <svg className="size-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
          </svg>
        </button>
      ) : null}
    </div>
  );
}
