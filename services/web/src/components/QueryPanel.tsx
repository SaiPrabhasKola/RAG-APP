import { useState } from "react";

import type { DocumentSummary } from "../api/types";
import { Spinner } from "./Spinner";

interface QueryPanelProps {
  loading: boolean;
  selectedDocument: DocumentSummary | null;
  onAsk: (query: string, topK: number) => void;
  onClearScope: () => void;
}

export function QueryPanel({
  loading,
  selectedDocument,
  onAsk,
  onClearScope,
}: QueryPanelProps) {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);

  const canSubmit = query.trim().length > 0 && !loading;

  function submit() {
    if (!canSubmit) {
      return;
    }

    onAsk(query.trim(), topK);
  }

  return (
    <div className="space-y-2.5">
      {selectedDocument ? (
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-500">Asking within</span>
          <span className="inline-flex max-w-[min(100%,28rem)] items-center gap-1 rounded-full bg-indigo-100 py-1 pl-2.5 pr-1 font-medium text-indigo-800">
            <span className="truncate">{selectedDocument.filename}</span>
            <button
              type="button"
              onClick={onClearScope}
              aria-label="Clear document scope"
              className="rounded-full p-0.5 transition hover:bg-indigo-200"
            >
              <svg className="size-3.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
              </svg>
            </button>
          </span>
        </div>
      ) : (
        <p className="text-xs text-slate-500">Asking across every indexed document.</p>
      )}

      <div className="rounded-xl border border-slate-200 bg-white shadow-sm transition focus-within:border-indigo-300 focus-within:ring-2 focus-within:ring-indigo-100">
        <label htmlFor="query-input" className="sr-only">
          Your question
        </label>
        <textarea
          id="query-input"
          value={query}
          rows={3}
          placeholder="Ask something answerable from your documents…"
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
              event.preventDefault();
              submit();
            }
          }}
          className="w-full resize-y rounded-t-xl bg-transparent px-4 py-3 text-sm text-slate-800 outline-none placeholder:text-slate-400"
        />

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-4 py-2.5">
          <div className="flex items-center gap-2">
            <label htmlFor="topk-input" className="text-xs font-medium text-slate-600">
              Sources
            </label>
            <input
              id="topk-input"
              type="range"
              min={1}
              max={20}
              value={topK}
              onChange={(event) => setTopK(Number(event.target.value))}
              className="h-1.5 w-28 cursor-pointer accent-indigo-600"
            />
            <span className="w-6 text-xs tabular-nums text-slate-500">{topK}</span>
          </div>

          <div className="flex items-center gap-3">
            <span className="hidden text-xs text-slate-400 sm:inline">⌘/Ctrl + ↵</span>
            <button
              type="button"
              onClick={submit}
              disabled={!canSubmit}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3.5 py-1.5 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {loading ? <Spinner className="size-4" /> : null}
              {loading ? "Searching…" : "Ask"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
