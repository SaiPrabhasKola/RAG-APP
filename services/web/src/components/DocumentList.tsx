import type { DocumentSummary } from "../api/types";
import { formatBytes, formatDate, shortId } from "../lib/format";
import { badgeFor, deriveDocumentState, isPendingState } from "../lib/status";
import { Spinner } from "./Spinner";

interface DocumentListProps {
  documents: DocumentSummary[];
  chunkCounts: Record<string, number>;
  loading: boolean;
  selectedDocId: string | null;
  deletingId: string | null;
  onSelect: (docId: string | null) => void;
  onDelete: (document: DocumentSummary) => void;
}

export function DocumentList({
  documents,
  chunkCounts,
  loading,
  selectedDocId,
  deletingId,
  onSelect,
  onDelete,
}: DocumentListProps) {
  if (loading && documents.length === 0) {
    return (
      <div className="flex items-center gap-2 px-1 py-6 text-sm text-slate-500">
        <Spinner className="size-4" />
        Loading documents…
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500">
        No documents yet — upload a PDF to get started.
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {documents.map((document) => {
        const selected = document.doc_id === selectedDocId;
        const deleting = document.doc_id === deletingId;
        const chunkCount = chunkCounts[document.doc_id];
        const state = deriveDocumentState(document, chunkCount);
        const badge = badgeFor(state, chunkCount);

        return (
          <li key={document.doc_id}>
            <div
              className={`flex items-start gap-2 rounded-lg border px-3 py-2.5 transition ${
                selected
                  ? "border-indigo-300 bg-indigo-50 ring-1 ring-indigo-200"
                  : "border-slate-200 bg-white hover:border-slate-300"
              }`}
            >
              <button
                type="button"
                onClick={() => onSelect(selected ? null : document.doc_id)}
                aria-pressed={selected}
                title={
                  selected
                    ? "Stop scoping questions to this document"
                    : "Scope questions to this document"
                }
                className="flex-1 text-left"
              >
                <p className="truncate text-sm font-medium text-slate-800">{document.filename}</p>

                <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-slate-500">
                  <span
                    className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 font-medium ${badge.className}`}
                    title={badge.title}
                  >
                    {isPendingState(state) ? <Spinner className="size-2.5" /> : null}
                    {badge.label}
                  </span>
                  <span>{formatBytes(document.size)}</span>
                  <span>{formatDate(document.created_at)}</span>
                  <span className="font-mono text-[10px] text-slate-400">
                    {shortId(document.doc_id)}
                  </span>
                </p>
              </button>

              <button
                type="button"
                onClick={() => onDelete(document)}
                disabled={deleting}
                aria-label={`Delete ${document.filename}`}
                className="rounded p-1.5 text-slate-400 transition hover:bg-rose-50 hover:text-rose-600 disabled:opacity-50"
              >
                {deleting ? (
                  <Spinner className="size-4" />
                ) : (
                  <svg className="size-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                    <path
                      fillRule="evenodd"
                      d="M8.75 1a.75.75 0 0 0-.75.75V3H4.25a.75.75 0 0 0 0 1.5h11.5a.75.75 0 0 0 0-1.5H12V1.75a.75.75 0 0 0-.75-.75h-2.5ZM5.5 6.5v8.75A1.75 1.75 0 0 0 7.25 17h5.5a1.75 1.75 0 0 0 1.75-1.75V6.5h-9Z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </button>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
