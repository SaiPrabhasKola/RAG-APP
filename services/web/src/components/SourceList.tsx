import { useState } from "react";

import type { Source } from "../api/types";
import { formatScore, shortId } from "../lib/format";

interface SourceListProps {
  sources: Source[];
  activeSourceId: number | null;
}

interface SourceCardProps {
  source: Source;
  active: boolean;
}

function SourceCard({ source, active }: SourceCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <li
      id={`source-${source.id}`}
      className={`scroll-mt-5 rounded-lg border bg-white px-3.5 py-3 transition ${
        active ? "border-indigo-400 ring-2 ring-indigo-100" : "border-slate-200"
      }`}
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs">
        <span className="inline-flex size-5 items-center justify-center rounded bg-indigo-100 font-semibold text-indigo-700">
          {source.id}
        </span>

        <span className="text-slate-600">
          page <span className="font-medium tabular-nums text-slate-800">{source.page_number}</span>
        </span>
        <span className="text-slate-600">
          chunk <span className="font-medium tabular-nums text-slate-800">{source.chunk_index}</span>
        </span>

        <span className="font-mono text-[10px] text-slate-400" title={source.document_id}>
          {shortId(source.document_id)}
        </span>

        <span className="ml-auto flex items-center gap-3 tabular-nums text-slate-500">
          <span title="Vector similarity score from Qdrant">
            sim {formatScore(source.score)}
          </span>
          <span title="Cross-encoder rerank score (bge-reranker-base)">
            rerank {formatScore(source.rerank_score)}
          </span>
        </span>
      </div>

      <p
        className={`mt-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-600 ${
          expanded ? "" : "line-clamp-3"
        }`}
      >
        {source.text}
      </p>

      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        className="mt-1.5 text-xs font-medium text-indigo-600 transition hover:text-indigo-800"
      >
        {expanded ? "Show less" : "Show more"}
      </button>
    </li>
  );
}

export function SourceList({ sources, activeSourceId }: SourceListProps) {
  if (sources.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 px-4 py-5 text-sm text-slate-500">
        <p className="font-medium text-slate-600">No sources returned.</p>
        <p className="mt-1">
          If you just uploaded a document it may still be processing — check its badge in the
          documents panel. Otherwise the question may not be covered by the indexed content.
        </p>
      </div>
    );
  }

  return (
    <ul className="space-y-2">
      {sources.map((source) => (
        <SourceCard key={source.id} source={source} active={source.id === activeSourceId} />
      ))}
    </ul>
  );
}
