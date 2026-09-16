# RAG-APP

A retrieval-augmented generation system over your own PDFs, built as independently
deployable services. Upload a PDF, it gets extracted, chunked and embedded in the
background; then you can ask questions and get answers grounded in the retrieved
chunks, with every claim cited back to a page and chunk.

```
┌───────────┐
│  Browser  │  React + Vite  (:5173)
└─────┬─────┘
      │
      │ 1. upload PDF                   2. ask a question
      ▼                                 ▼
┌──────────────────┐            ┌──────────────────┐
│ document-service │            │  query-service   │ :8003
│      :8000       │            └────┬─────────┬───┘
└───┬──────────┬───┘                 │         │
    │          │                     │         │
    │          └─► MinIO             │         └─► generation-service :8004
    │              (documents)       │                └─► Gemini
    │                                │
    │  publish                       │
    ▼                                ▼
┌────────────────────┐       ┌──────────────────┐      ┌────────────┐
│ [document.process] │       │ retrieval-service│─────►│            │
└─────────┬──────────┘       │      :8002       │      │   Qdrant   │
          ▼                  └──────────────────┘      │   :6333    │
┌────────────────────────┐                            │  (768d)    │
│ document-process-worker│                            └──────┬─────┘
│  PyMuPDF → chunk       │                                   │
└─────────┬──────────────┘                                   │
          │ publish                                          │
          ▼                                                  │
   [document.embed]                                          │
          ▼                                                  │
┌────────────────────┐                                       │
│ embedding-service  │───────────────────────────────────────┘
│ bge-base-en-v1.5   │
└────────────────────┘
```

## Services

| Service | Port | Role | Key libraries |
|---|---|---|---|
| `services/web` | 5173 | React + Vite + Tailwind frontend | React 19, Vite, Tailwind 4 |
| `services/document-service` | 8000 | PDF upload, document metadata, status | FastAPI, SQLAlchemy, MinIO, pika |
| `services/document-process-worker` | — | Extracts text, chunks it, fans out to embedding | PyMuPDF, langchain-text-splitters, pika |
| `services/embedding-service` | — | Embeds chunks and upserts them into Qdrant | sentence-transformers, qdrant-client, pika |
| `services/retrieval-service` | 8002 | Vector search + cross-encoder rerank, chunk counts | qdrant-client, sentence-transformers |
| `services/generation-service` | 8004 | Builds the RAG prompt and calls Gemini | google-genai |
| `services/query-service` | 8003 | Orchestrates retrieve → generate, Redis cache | FastAPI, httpx, redis |
| `services/gateway` | — | **Empty placeholder** | — |
| `services/identity-service` | — | **Empty placeholder** | — |

Infrastructure (from `docker-compose.yml`):

| Container | Port | Purpose |
|---|---|---|
| `postgres` | 5432 | Document metadata (`documents` table) |
| `rabbitmq` | 5672, 15672 | Job queues; management UI at http://localhost:15672 |
| `redis` | 6379 | Query response cache |
| `qdrant` | 6333 | Vector store (`document_chunks` collection) |
| `minio` | internal only | Object storage for original PDFs |

Only **8000, 8002, 8003, 8004, 5173** and the infra ports are published to the host.
`embedding-service` and `document-process-worker` are pure RabbitMQ consumers with no HTTP
server — they cannot be reached with a request. `minio` publishes no host port, so the browser
cannot link directly to an uploaded PDF.

## How it works

**Ingest** — `POST /documents` streams the PDF to MinIO and publishes
`{document_id, object_key}` to the durable `document.process` queue, returning `202` immediately.
The worker pulls it, extracts text page by page with PyMuPDF, normalises it (NFKC, de-hyphenation,
whitespace collapsing), splits it into section-aware chunks, and publishes one `document.embed`
message per chunk. The embedding service vectorises each chunk with `BAAI/bge-base-en-v1.5`
(768d, normalised) and upserts it into Qdrant.

**Chunking** is boundary-aware rather than fixed-width. Lines that look like section headings
(`EXPERIENCE`, `PROJECTS`, known résumé headings, markdown `#`) and subsection/project titles
(starting a hard new boundary), and no chunk ever spans two sections or two projects. Each chunk
carries its section/subsection as a header prepended to the text, so retrieved chunks are
self-describing. Within a boundary, `RecursiveCharacterTextSplitter` (size 700, overlap 150)
prefers paragraph → line → bullet → sentence breaks.

**Query** — `POST /query` on `query-service` first checks Redis. On a miss it calls
`retrieval-service`, which embeds the query (prefixed with
`Represent this sentence for searching relevant passages: `), pulls `max(top_k * 4, 20)`
candidates from Qdrant with cosine similarity, reranks them with the `BAAI/bge-reranker-base`
cross-encoder, and returns the top `top_k`. `query-service` numbers the results 1..N, passes them
to `generation-service`, which builds a strictly-grounded prompt and calls `gemini-3.6-flash`.
The response is cached for 300 s.

Because Qdrant point IDs are deterministic —
`uuid5(NAMESPACE_URL, "{document_id}:{page_number}:{chunk_index}")` — re-processing a document
overwrites its existing points instead of duplicating them.

## Document statuses

The worker reports progress back to `document-service` via `PATCH /documents/{id}/status`, which
only accepts `processing`, `empty` or `failed`. "Ready" is **not** a stored status: it is derived
from the number of chunks actually present in Qdrant, which is the only true signal that embedding
finished.

| Badge | Meaning |
|---|---|
| `Queued` | Accepted, not yet picked up by a worker |
| `Processing` | Worker is extracting/chunking; embedding may still be running |
| `Ready · N chunks` | N chunks are in Qdrant and searchable |
| `No text extracted` | Terminal — chunking produced 0 chunks (usually a scanned PDF with no text layer) |
| `Failed` | Terminal — the worker raised an error |
| `Not searchable` | No chunks ever landed and the pipeline has had ample time |

The frontend polls `POST /documents/chunk-counts` (batched) plus a silent document-list refresh
every 2 s, but only while something is unsettled. Reaching any terminal state stops the polling.

## Prerequisites

- Docker Desktop
- Node.js 20+ (developed against 22) for the frontend
- Python 3.14 if you want to run services outside Docker
- A Google Gemini API key

## Quick start

1. **Create the Gemini key file** — without it `generation-service` fails to start, because
   `gemini_api_key` is a required setting:

   ```bash
   # services/generation-service/.env
   GEMINI_API_KEY=your-key-here
   ```

2. **Start the backend:**

   ```bash
   docker compose up -d --build
   ```

   First build downloads the sentence-transformers models; the embedding and retrieval services
   take ~30 s to become ready while the models load.

3. **Start the frontend:**

   ```bash
   cd services/web
   npm install
   npm run dev
   ```

4. Open http://localhost:5173

`services/query-service/.env` already exists with the defaults it needs
(`RETRIEVAL_SERVICE_URL`, `GENERATION_SERVICE_URL`, `REDIS_URL`). It is gitignored.

## Frontend

```
services/web/
├── .env                 service URLs (gitignored); all have localhost fallbacks
├── .env.example         the same keys, documented
├── vite.config.ts       port 5173 with strictPort
└── src/
    ├── App.tsx          layout + all state (no global store)
    ├── api/client.ts    typed fetch wrappers, errors normalised to ApiError
    ├── hooks/           useDocuments, useDocumentStatus (polling), useQuery
    ├── lib/status.ts    chunk count + worker status → badge state
    └── components/      upload, list, query panel, answer, sources
```

| Variable | Default | Used for |
|---|---|---|
| `VITE_DOCUMENT_SERVICE_URL` | `http://localhost:8000` | upload, list, delete, status |
| `VITE_QUERY_SERVICE_URL` | `http://localhost:8003` | asking questions |
| `VITE_RETRIEVAL_SERVICE_URL` | `http://localhost:8002` | chunk counts for the badges |

Three UI behaviours are deliberate:

- The backend's own error text is surfaced verbatim, so a downed service shows
  `Could not connect to generation service` rather than a generic failure.
- Any identical query answered in under 150 ms is marked `cached`, because `query-service` serves
  repeats from a 300 s Redis cache and an instant answer otherwise looks broken.
- A citation like `[1]` in an answer is a button that scrolls to and highlights that source card.

## API

### document-service `:8000`

| Method | Path | Notes |
|---|---|---|
| `POST` | `/documents` | `multipart/form-data`, field name **`file`**, PDF only. `202 {doc_id, status}`. Rejects non-PDF with `400`. |
| `GET` | `/documents` | `?limit=50&offset=0`, newest first. Returns `doc_id, filename, content_type, size, status, created_at`. |
| `GET` | `/documents/{doc_id}` | One document, or `404`. |
| `DELETE` | `/documents/{doc_id}` | `204`. Removes the DB row and the MinIO object. **Does not remove vectors** — see Limitations. |
| `PATCH` | `/documents/{doc_id}/status` | Body `{"status": "processing"\|"empty"\|"failed"}`. Anything else is `422`. Called by the worker. |
| `GET` | `/health` | `{"status":"Ok"}` |
| `GET` | `/storage-health` | Bucket list; `500` if MinIO is unreachable. |

### retrieval-service `:8002`

| Method | Path | Notes |
|---|---|---|
| `POST` | `/retrieve` | `{query, top_k=5, document_id?}` → `{results: [{score, rerank_score, document_id, page_number, chunk_index, text}]}`. No `id` field. |
| `POST` | `/documents/chunk-counts` | `{document_ids: [...]}` → `{counts: {doc_id: n}}`. Capped at 100 ids. Counts 0 rather than failing if Qdrant errors. |

### generation-service `:8004`

| Method | Path | Notes |
|---|---|---|
| `POST` | `/generate` | `{query, sources: [Source]}` → `{query, answer, sources}`. All seven `Source` fields are required. Non-streaming. |

### query-service `:8003`

| Method | Path | Notes |
|---|---|---|
| `POST` | `/query` | `{query, top_k=5, document_id?}` → `{query, answer, sources: [{id, document_id, page_number, chunk_index, text, score, rerank_score}]}`. Assigns the 1-based `id`. |

Returns `502`/`504` with a `detail` string when retrieval or generation is unreachable, after
3 attempts with exponential backoff. Cached responses are byte-identical to the original, so their
source `id`s come from the original run.

## Running services outside Docker

Each service keeps its own virtual environment, so a change to one service's dependencies cannot
affect another:

```powershell
cd services/retrieval-service
py -3.14 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --port 8002
```

The workers start with `python -m app.main` instead of uvicorn. Point them at the published infra
ports (`localhost:5432`, `localhost:6379`, `localhost:6333`, `amqp://rag:rag@localhost:5672/`) —
the defaults in `app/config.py` already do this. Note that `document-service` and
`retrieval-service` read plain environment variables, while `query-service` and
`generation-service` load a local `.env`.

## CORS

No service allows cross-origin requests by default except through an explicit allowlist:

```
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:4173
```

Set per service in `docker-compose.yml`. Origins are matched exactly and never `"*"`, so serving
the frontend from another port requires adding it here — which is also why the Vite dev server
uses `strictPort` (a silent fallback to 5174 would fail every request).

## Retrieval evaluation

`evaluation/evaluate_retrieval.py` measures recall@1/3/5 for ten hand-labelled questions against a
single document. It talks to a running `retrieval-service` and expects that document to already be
indexed:

```bash
python evaluation/evaluate_retrieval.py
```

Set `DOCUMENT_ID` at the top of the file to the document you want to evaluate.

## Limitations and known issues

- **Deleting a document leaves its embeddings in Qdrant.** They keep showing up as sources in
  answers. Cleaning them up requires a filter-delete against Qdrant, which belongs in
  retrieval-service (it owns the collection) — not implemented yet. The UI's confirm dialog says
  so explicitly.
- **`document_id` has no Qdrant payload index**, so every chunk-count and retrieval filter is a
  full collection scan. Fine at a few hundred points; it will not scale. Fix by creating a
  `keyword` payload index on `document_id` in `ensure_collection()`.
- **The worker retries failures forever.** On exception it calls `basic_nack(requeue=True)`, so a
  poison PDF loops indefinitely. It reports `failed` first, but the retry overwrites that with
  `processing`, and there is no dead-letter queue.
- **`size` is always 0.** `create_document()` hardcodes it, so the UI shows `—`. `UploadFile.size`
  is available if you want to record it.
- **Nothing streams.** `/generate` and `/query` await the whole LLM response. There is no SSE
  endpoint.
- **No authentication anywhere.** Every endpoint, including delete, is open. Fine for a local tool.
- **`ALLOWED_ORIGINS` exists per service**, so the same snippet is duplicated across four
  `main.py` files. Chosen over a shared helper because the services are deliberately independent
  and their config modules differ.
- `packages/common`, `packages/events`, `infrastructure` and the two placeholder services are empty.

## Repository layout

```
.
├── docker-compose.yml
├── RAG-APP.code-workspace     multi-root workspace, one folder per service
├── evaluation/                retrieval quality harness
├── packages/                  (empty) shared code, not yet used
└── services/
    ├── document-service/
    ├── document-process-worker/
    ├── embedding-service/
    ├── retrieval-service/
    ├── generation-service/
    ├── query-service/
    ├── web/
    ├── gateway/               (empty)
    └── identity-service/      (empty)
```

Each Python service follows the same shape: `app/` with `config.py` (pydantic-settings),
`main.py` (or `consumer.py` for workers), `schemas.py`, a per-service `.venv/` and
`requirements.txt`.

## Troubleshooting

**`document-service` won't start / `relation "documents" does not exist`**
The table is created at import time via `Base.metadata.create_all`. Check the Postgres
healthcheck passed and `DATABASE_URL` is correct.

**Everything 502s from the frontend**
Requests are being blocked by CORS. Check the browser console for a preflight failure and confirm
your origin is in `ALLOWED_ORIGINS` for the service being called.

**Uploads succeed but questions return no sources**
Processing is asynchronous. Check the document's badge; if it is `No text extracted`, the PDF has
no text layer (scanned images) and OCR is not implemented. Otherwise watch
`docker compose logs -f document-process-worker embedding-service`.

**The first query after starting takes a long time**
Embedding and retrieval services load sentence-transformers models on startup (~30 s), and the
embedding service reloads them if restarted. A sustained `Processing` badge during that window is
expected.

**Answers say "I don't have enough information in the provided documents to answer that."**
That is the prompt's grounding guardrail firing — it answers only from retrieved context. Either
retrieval did not surface a relevant chunk, or the model judged the context insufficient. Check
the returned sources and their `sim`/`rerank` scores.
