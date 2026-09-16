import { useRef, useState } from "react";

import { uploadDocument, toUiError } from "../api/client";
import type { UiError } from "../api/types";
import { ErrorBanner } from "./ErrorBanner";
import { Spinner } from "./Spinner";

interface DocumentUploadProps {
  onUploaded: (filename: string) => void;
}

const PDF_MIME = "application/pdf";

function isPdf(file: File): boolean {
  return file.type === PDF_MIME || file.name.toLowerCase().endsWith(".pdf");
}

export function DocumentUpload({ onUploaded }: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<UiError | null>(null);

  async function send(file: File) {
    setError(null);

    if (!isPdf(file)) {
      setError({ message: `"${file.name}" is not a PDF. Only PDFs can be indexed.`, status: -1 });
      return;
    }

    setUploading(true);

    try {
      await uploadDocument(file);
      onUploaded(file.name);
    } catch (cause) {
      setError(toUiError(cause, "The upload failed."));
    } finally {
      setUploading(false);

      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  }

  return (
    <div className="space-y-3">
      <label
        htmlFor="pdf-input"
        onDragOver={(event) => {
          event.preventDefault();
          if (!uploading) {
            setDragging(true);
          }
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);

          if (uploading) {
            return;
          }

          const file = event.dataTransfer.files[0];

          if (file) {
            void send(file);
          }
        }}
        className={`flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-4 py-6 text-center transition ${
          dragging
            ? "border-indigo-400 bg-indigo-50"
            : "border-slate-300 bg-slate-50 hover:border-indigo-300 hover:bg-indigo-50/40"
        } ${uploading ? "cursor-wait opacity-70" : "cursor-pointer"}`}
      >
        {uploading ? (
          <Spinner className="size-6 text-indigo-600" />
        ) : (
          <svg
            className="size-6 text-slate-400"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            aria-hidden="true"
          >
            <path d="M12 16V4m0 0L8 8m4-4 4 4" strokeLinecap="round" strokeLinejoin="round" />
            <path
              d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}

        <span className="text-sm font-medium text-slate-700">
          {uploading ? "Uploading…" : "Drop a PDF here, or click to browse"}
        </span>
        <span className="text-xs text-slate-500">
          PDF only · text is extracted and embedded in the background
        </span>

        <input
          id="pdf-input"
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="sr-only"
          disabled={uploading}
          onChange={(event) => {
            const file = event.target.files?.[0];

            if (file) {
              void send(file);
            }
          }}
        />
      </label>

      {error ? <ErrorBanner error={error} onDismiss={() => setError(null)} /> : null}
    </div>
  );
}
