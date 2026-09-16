import { useCallback, useState } from "react";

import { deleteDocument, toUiError } from "./api/client";
import type { DocumentSummary, UiError } from "./api/types";
import { AnswerCard } from "./components/AnswerCard";
import { DocumentPanel } from "./components/DocumentPanel";
import { ErrorBanner } from "./components/ErrorBanner";
import { HealthBadge } from "./components/HealthBadge";
import { QueryPanel } from "./components/QueryPanel";
import { SourceList } from "./components/SourceList";
import { useDocuments } from "./hooks/useDocuments";
import { useDocumentStatus } from "./hooks/useDocumentStatus";
import { useQuery } from "./hooks/useQuery";

function EmptyState({ hasDocuments }: { hasDocuments: boolean }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white px-5 py-8 text-center">
      <h2 className="text-sm font-medium text-slate-700">
        {hasDocuments ? "Ask a question to get started" : "Upload a PDF to get started"}
      </h2>
      <p className="mx-auto mt-1.5 max-w-md text-sm text-slate-500">
        {hasDocuments
          ? "Answers are grounded in the chunks retrieved from Qdrant, and each citation links back to the page and chunk it came from."
          : "Once uploaded, a document is extracted, chunked and embedded in the background. After that you can ask questions about it here."}
      </p>
    </div>
  );
}

export default function App() {
  const { documents, loading, error: documentsError, refresh } = useDocuments();
  const chunkCounts = useDocumentStatus(documents, refresh);
  const { result, loading: asking, error: queryError, ask } = useQuery();

  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<UiError | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [activeSourceId, setActiveSourceId] = useState<number | null>(null);

  const selectedDocument =
    documents.find((document) => document.doc_id === selectedDocId) ?? null;

  const handleUploaded = useCallback(
    async (filename: string) => {
      setNotice(
        `"${filename}" uploaded. Extracting and embedding in the background — the badge updates on its own once it is searchable.`,
      );
      setActionError(null);
      await refresh();
    },
    [refresh],
  );

  const handleDelete = useCallback(
    async (document: DocumentSummary) => {
      const confirmed = window.confirm(
        `Delete "${document.filename}"?\n\nThis removes the stored PDF and its metadata. Its embeddings are NOT removed from the vector store, so the document may still appear in answers.`,
      );

      if (!confirmed) {
        return;
      }

      setDeletingId(document.doc_id);
      setActionError(null);

      try {
        await deleteDocument(document.doc_id);
        setSelectedDocId((current) => (current === document.doc_id ? null : current));
        setNotice(`"${document.filename}" deleted.`);
        await refresh();
      } catch (cause) {
        setActionError(toUiError(cause, "Failed to delete the document."));
      } finally {
        setDeletingId(null);
      }
    },
    [refresh],
  );

  const handleAsk = useCallback(
    async (query: string, topK: number) => {
      setActiveSourceId(null);
      await ask(query, topK, selectedDocId);
    },
    [ask, selectedDocId],
  );

  const handleCitationClick = useCallback((sourceId: number) => {
    setActiveSourceId(sourceId);
    window.document.getElementById(`source-${sourceId}`)?.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-5 py-3.5">
          <div className="flex items-baseline gap-2.5">
            <h1 className="text-base font-semibold tracking-tight">RAG</h1>
            <p className="text-xs text-slate-500">Ask questions across your indexed PDFs</p>
          </div>

          <HealthBadge />
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl items-start gap-5 px-5 py-5 lg:grid-cols-[22rem_minmax(0,1fr)]">
        <DocumentPanel
          documents={documents}
          chunkCounts={chunkCounts}
          loading={loading}
          error={documentsError}
          selectedDocId={selectedDocId}
          deletingId={deletingId}
          notice={notice}
          onRefresh={() => void refresh()}
          onSelect={setSelectedDocId}
          onDelete={(document) => void handleDelete(document)}
          onUploaded={(filename) => void handleUploaded(filename)}
          onDismissNotice={() => setNotice(null)}
        />

        <div className="space-y-4">
          <QueryPanel
            loading={asking}
            selectedDocument={selectedDocument}
            onAsk={(query, topK) => void handleAsk(query, topK)}
            onClearScope={() => setSelectedDocId(null)}
          />

          {actionError ? (
            <ErrorBanner error={actionError} onDismiss={() => setActionError(null)} />
          ) : null}

          {queryError ? <ErrorBanner error={queryError} /> : null}

          {result ? (
            <>
              <AnswerCard result={result} onCitationClick={handleCitationClick} />

              <section className="space-y-2">
                <h2 className="px-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Retrieved sources
                </h2>
                <SourceList sources={result.sources} activeSourceId={activeSourceId} />
              </section>
            </>
          ) : !asking && !queryError ? (
            <EmptyState hasDocuments={documents.length > 0} />
          ) : null}
        </div>
      </main>
    </div>
  );
}
