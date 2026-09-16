/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_DOCUMENT_SERVICE_URL?: string;
  readonly VITE_QUERY_SERVICE_URL?: string;
  readonly VITE_RETRIEVAL_SERVICE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
