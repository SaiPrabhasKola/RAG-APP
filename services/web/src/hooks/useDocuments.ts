import { useCallback, useEffect, useState } from "react";

import { listDocuments, toUiError } from "../api/client";
import type { DocumentSummary, UiError } from "../api/types";
import type { RefreshOptions } from "./useDocumentStatus";

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<UiError | null>(null);

  const refresh = useCallback(async (options?: RefreshOptions) => {
    const silent = options?.silent ?? false;

    if (!silent) {
      setLoading(true);
    }

    try {
      setDocuments(await listDocuments());
      setError(null);
    } catch (cause) {
      // A silent (polling) refresh must not flash an error banner for a blip.
      if (!silent) {
        setError(toUiError(cause, "Failed to load documents."));
      }
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { documents, loading, error, refresh };
}
