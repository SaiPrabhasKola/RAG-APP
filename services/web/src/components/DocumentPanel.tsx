import type { DocumentSummary, UiError } from "../api/types";
import { DocumentList } from "./DocumentList";
import { DocumentUpload } from "./DocumentUpload";
import { ErrorBanner } from "./ErrorBanner";
import { Spinner } from "./Spinner";

interface DocumentPanelProps {
  documents: DocumentSummary[];
  chunkCounts: Record<string, number>;
  loading: boolean;
  error: UiError | null;
  selectedDocId: string | null;
  deletingId: string | null;
  notice: string | null;
  onRefresh: () => void;
  onSelect: (docId: string | null) => void;
  onDelete: (document: DocumentSummary) => void;
  onUploaded: (filename: string) => void;
  onDismissNotice: () => void;
}

export function DocumentPanel({
  documents,
  chunkCounts,
  loading,
  error,
  selectedDocId,
  deletingId,
  notice,
  onRefresh,
  onSelect,
  onDelete,
  onUploaded,
  onDismissNotice,
}: DocumentPanelProps) {
  return (
    <aside>
      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <header className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-800">Documents</h2>

          <button
            type="button"
            onClick={onRefresh}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 disabled:opacity-50"
          >
            <svg
              className="size-3.5"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              aria-hidden="true"
            >
              <path
                d="M16 10a6 6 0 1 1-1.8-4.3M16 3v3.5h-3.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            Refresh
          </button>
        </header>

        <DocumentUpload onUploaded={onUploaded} />

        {notice ? (
          <div className="mt-3 flex items-start gap-2.5 rounded-lg border border-amber-200 bg-amber-50 px-3.5 py-2.5 text-xs text-amber-900">
            <span className="flex-1">{notice}</span>
            <button
              type="button"
              onClick={onDismissNotice}
              aria-label="Dismiss notice"
              className="rounded p-0.5 text-amber-600 transition hover:bg-amber-100"
            >
              <svg className="size-3.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
              </svg>
            </button>
          </div>
        ) : null}

        {error ? (
          <div className="mt-3">
            <ErrorBanner error={error} />
          </div>
        ) : null}

        <div className="mt-4">
          <DocumentList
            documents={documents}
            chunkCounts={chunkCounts}
            loading={loading}
            selectedDocId={selectedDocId}
            deletingId={deletingId}
            onSelect={onSelect}
            onDelete={onDelete}
          />
        </div>

        {loading && documents.length > 0 ? (
          <p className="mt-2 flex items-center gap-1.5 text-xs text-slate-400">
            <Spinner className="size-3" />
            Refreshing…
          </p>
        ) : null}
      </section>
    </aside>
  );
}
