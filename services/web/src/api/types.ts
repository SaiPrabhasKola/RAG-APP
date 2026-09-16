export interface DocumentSummary {
  doc_id: string;
  filename: string;
  content_type: string;
  size: number;
  status: string;
  created_at: string;
}

export interface Source {
  id: number;
  document_id: string;
  page_number: number;
  chunk_index: number;
  text: string;
  score: number;
  rerank_score: number;
}

export interface QueryResponse {
  query: string;
  answer: string;
  sources: Source[];
}

export interface QueryResult extends QueryResponse {
  cached: boolean;
  durationMs: number;
}

export interface UploadResponse {
  doc_id: string;
  status: string;
}

export interface HealthResponse {
  status: string;
}

export interface ChunkCountsResponse {
  counts: Record<string, number>;
}

export interface UiError {
  message: string;
  status: number;
}
