import type { ReactNode } from "react";

import type { QueryResult } from "../api/types";
import { formatDuration } from "../lib/format";

interface AnswerCardProps {
  result: QueryResult;
  onCitationClick: (sourceId: number) => void;
}

function renderAnswer(answer: string, onCitationClick: (sourceId: number) => void): ReactNode[] {
  const nodes: ReactNode[] = [];
  const pattern = /\[(\d+)\]/g;
  let lastIndex = 0;
  let match = pattern.exec(answer);

  while (match !== null) {
    if (match.index > lastIndex) {
      nodes.push(answer.slice(lastIndex, match.index));
    }

    const sourceId = Number(match[1]);

    nodes.push(
      <button
        key={`${sourceId}-${match.index}`}
        type="button"
        onClick={() => onCitationClick(sourceId)}
        aria-label={`Jump to source ${sourceId}`}
        className="mx-0.5 inline-flex size-5 items-center justify-center rounded bg-indigo-100 align-super text-[11px] font-semibold text-indigo-700 transition hover:bg-indigo-200"
      >
        {sourceId}
      </button>,
    );

    lastIndex = pattern.lastIndex;
    match = pattern.exec(answer);
  }

  if (lastIndex < answer.length) {
    nodes.push(answer.slice(lastIndex));
  }

  return nodes;
}

export function AnswerCard({ result, onCitationClick }: AnswerCardProps) {
  return (
    <section
      aria-live="polite"
      className="rounded-xl border border-slate-200 bg-white shadow-sm"
    >
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 px-4 py-3">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-slate-800">Answer</h2>

          {result.cached ? (
            <span
              className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600"
              title="Returned instantly — served from query-service's 300s Redis cache."
            >
              cached
            </span>
          ) : null}
        </div>

        <div className="flex items-center gap-3 text-xs text-slate-500">
          <span>
            {result.sources.length} source{result.sources.length === 1 ? "" : "s"}
          </span>
          <span className="tabular-nums">{formatDuration(result.durationMs)}</span>
        </div>
      </header>

      <div className="whitespace-pre-wrap px-4 py-3.5 text-sm leading-relaxed text-slate-700">
        {renderAnswer(result.answer, onCitationClick)}
      </div>
    </section>
  );
}
