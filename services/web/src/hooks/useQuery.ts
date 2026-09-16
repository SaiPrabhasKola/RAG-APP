import { useCallback, useState } from "react";

import { askQuestion, toUiError } from "../api/client";
import type { QueryResult, UiError } from "../api/types";

const CACHE_HINT_THRESHOLD_MS = 150;

export function useQuery() {
  const [result, setResult] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<UiError | null>(null);

  const ask = useCallback(
    async (query: string, topK: number, documentId: string | null) => {
      setLoading(true);
      setError(null);

      const startedAt = performance.now();

      try {
        const response = await askQuestion({ query, topK, documentId });
        const durationMs = performance.now() - startedAt;

        setResult({
          ...response,
          durationMs,
          cached: durationMs < CACHE_HINT_THRESHOLD_MS,
        });
      } catch (cause) {
        setResult(null);
        setError(toUiError(cause, "The query failed."));
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  return { result, loading, error, ask };
}
