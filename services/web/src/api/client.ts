import type {
  ChunkCountsResponse,
  DocumentSummary,
  HealthResponse,
  QueryResponse,
  UiError,
  UploadResponse,
} from "./types";

const BASE = {
  documents: import.meta.env.VITE_DOCUMENT_SERVICE_URL ?? "http://localhost:8000",
  query: import.meta.env.VITE_QUERY_SERVICE_URL ?? "http://localhost:8003",
  retrieval: import.meta.env.VITE_RETRIEVAL_SERVICE_URL ?? "http://localhost:8002",
};

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function toUiError(cause: unknown, fallback: string): UiError {
  if (cause instanceof ApiError) {
    return { message: cause.message, status: cause.status };
  }

  return { message: fallback, status: -1 };
}

async function readDetail(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();

    if (body && typeof body === "object" && "detail" in body) {
      const detail = (body as { detail: unknown }).detail;

      if (typeof detail === "string") {
        return detail;
      }

      return JSON.stringify(detail);
    }
  } catch {
    // Empty or non-JSON body - fall through to the generic message.
  }

  return `Request failed with status ${response.status}.`;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(url, init);
  } catch {
    throw new ApiError(0, `Could not reach ${url}. Is the service running?`);
  }

  if (!response.ok) {
    throw new ApiError(response.status, await readDetail(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function listDocuments(): Promise<DocumentSummary[]> {
  return request<DocumentSummary[]>(`${BASE.documents}/documents`);
}

export function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return request<UploadResponse>(`${BASE.documents}/documents`, {
    method: "POST",
    body: formData,
  });
}

export function deleteDocument(docId: string): Promise<void> {
  return request<void>(`${BASE.documents}/documents/${docId}`, {
    method: "DELETE",
  });
}

export function checkHealth(): Promise<HealthResponse> {
  return request<HealthResponse>(`${BASE.documents}/health`);
}

export function getChunkCounts(
  documentIds: string[],
): Promise<Record<string, number>> {
  return request<ChunkCountsResponse>(`${BASE.retrieval}/documents/chunk-counts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_ids: documentIds }),
  }).then((response) => response.counts);
}

export interface AskOptions {
  query: string;
  topK: number;
  documentId: string | null;
}

export function askQuestion({
  query,
  topK,
  documentId,
}: AskOptions): Promise<QueryResponse> {
  return request<QueryResponse>(`${BASE.query}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      top_k: topK,
      document_id: documentId,
    }),
  });
}
