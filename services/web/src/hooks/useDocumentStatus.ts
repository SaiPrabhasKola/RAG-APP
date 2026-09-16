import { useEffect, useMemo, useRef, useState } from "react";

import { getChunkCounts } from "../api/client";
import type { DocumentSummary } from "../api/types";
import { deriveDocumentState, isPendingState } from "../lib/status";

const POLL_INTERVAL_MS = 2000;

export interface RefreshOptions {
  silent?: boolean;
}

/**
 * Keeps a per-document chunk count (read from Qdrant via retrieval-service),
 * which is the only signal that embedding has actually finished.
 *
 * A document is polled while either its count is unknown or its derived state
 * is still pending. Reaching "ready" (count > 0), "empty" or "failed" is
 * terminal, so polling stops by itself once nothing is in flight.
 */
export function useDocumentStatus(
  documents: DocumentSummary[],
  refreshDocuments: (options?: RefreshOptions) => Promise<void>,
) {
  const [chunkCounts, setChunkCounts] = useState<Record<string, number>>({});

  const polledIds = useMemo(
    () =>
      documents
        .filter((document) => {
          const count = chunkCounts[document.doc_id];

          if (count === undefined) {
            return true;
          }

          return isPendingState(deriveDocumentState(document, count));
        })
        .map((document) => document.doc_id),
    [documents, chunkCounts],
  );

  const polledRef = useRef<string[]>(polledIds);
  polledRef.current = polledIds;

  const polledKey = polledIds.join(",");

  useEffect(() => {
    if (polledKey === "") {
      return;
    }

    let active = true;

    async function tick() {
      const ids = polledRef.current;

      if (ids.length === 0) {
        return;
      }

      try {
        const counts = await getChunkCounts(ids);

        if (!active) {
          return;
        }

        setChunkCounts((previous) => ({ ...previous, ...counts }));
      } catch {
        // Transient - the next tick retries.
        return;
      }

      // Pick up worker-reported status transitions (processing/empty/failed).
      await refreshDocuments({ silent: true });
    }

    void tick();
    const timer = window.setInterval(() => void tick(), POLL_INTERVAL_MS);

    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [polledKey, refreshDocuments]);

  return chunkCounts;
}
