import type { DocumentSummary } from "../api/types";

export type DocumentState =
  | "queued"
  | "processing"
  | "ready"
  | "empty"
  | "failed"
  | "unsearchable";

const SETTLED_AFTER_MS = 2 * 60 * 1000;

export function deriveDocumentState(
  document: DocumentSummary,
  chunkCount: number | undefined,
): DocumentState {
  if ((chunkCount ?? 0) > 0) {
    return "ready";
  }

  if (document.status === "failed") {
    return "failed";
  }

  if (document.status === "empty") {
    return "empty";
  }

  if (document.status === "processing") {
    return "processing";
  }

  const createdAt = new Date(document.created_at).getTime();

  if (Number.isFinite(createdAt) && Date.now() - createdAt > SETTLED_AFTER_MS) {
    return "unsearchable";
  }

  return "queued";
}

export function isPendingState(state: DocumentState): boolean {
  return state === "queued" || state === "processing";
}

export interface Badge {
  label: string;
  className: string;
  title: string;
}

export function badgeFor(state: DocumentState, chunkCount: number | undefined): Badge {
  switch (state) {
    case "queued":
      return {
        label: "Queued",
        className: "bg-slate-100 text-slate-600",
        title: "Waiting for the processing worker to pick it up.",
      };

    case "processing":
      return {
        label: "Processing",
        className: "bg-amber-100 text-amber-800",
        title: "Extracting text and embedding chunks. This updates automatically.",
      };

    case "ready":
      return {
        label: `Ready · ${chunkCount ?? 0} chunk${chunkCount === 1 ? "" : "s"}`,
        className: "bg-emerald-100 text-emerald-800",
        title: "These chunks are in the vector store, so the document can be queried.",
      };

    case "empty":
      return {
        label: "No text extracted",
        className: "bg-slate-200 text-slate-700",
        title:
          "The worker finished but produced no chunks — the PDF is probably scanned images with no text layer.",
      };

    case "failed":
      return {
        label: "Failed",
        className: "bg-rose-100 text-rose-800",
        title:
          "The worker raised an error. The message is re-queued for retry — use Refresh to re-check.",
      };

    case "unsearchable":
      return {
        label: "Not searchable",
        className: "bg-slate-200 text-slate-700",
        title:
          "No chunks landed in the vector store, so this document cannot appear in answers.",
      };
  }
}
