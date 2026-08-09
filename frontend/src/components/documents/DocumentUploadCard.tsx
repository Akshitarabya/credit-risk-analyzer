import { useRef, useState } from "react";
import { FileText, Trash2, Upload } from "lucide-react";

import { deleteDocument, fetchDocumentFileBlob, uploadDocument } from "@/api/documents";
import DocumentStatusBadge from "@/components/documents/DocumentStatusBadge";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import { getErrorMessage } from "@/utils/errors";
import { formatDate } from "@/utils/format";
import type { DocumentSummary, DocumentType } from "@/types/document";

interface DocumentUploadCardProps {
  loanApplicationId: string;
  documentType: DocumentType;
  label: string;
  hint: string;
  document: DocumentSummary | null;
  onChanged: () => Promise<void> | void;
}

// Fast client-side feedback only — the backend independently re-validates
// every one of these by sniffing the actual file content, never trusting
// what the browser reports here.
const ACCEPTED_MIME_TYPES = ["image/jpeg", "image/png", "application/pdf"];
const MAX_SIZE_BYTES = 10 * 1024 * 1024;

function formatFileSize(bytes: number): string {
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentUploadCard({
  loanApplicationId,
  documentType,
  label,
  hint,
  document,
  onChanged,
}: DocumentUploadCardProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isViewing, setIsViewing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFileSelected(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = ""; // allow re-selecting the same file later
    if (!file) return;

    setError(null);

    if (!ACCEPTED_MIME_TYPES.includes(file.type)) {
      setError("Only JPEG, PNG, or PDF files are accepted.");
      return;
    }
    if (file.size > MAX_SIZE_BYTES) {
      setError("File is larger than the 10 MB limit.");
      return;
    }

    setIsUploading(true);
    try {
      await uploadDocument(loanApplicationId, documentType, file);
      await onChanged();
    } catch (err) {
      setError(getErrorMessage(err, "Could not upload this file."));
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDelete() {
    if (!document) return;
    setError(null);
    setIsDeleting(true);
    try {
      await deleteDocument(loanApplicationId, document.id);
      await onChanged();
    } catch (err) {
      setError(getErrorMessage(err, "Could not delete this document."));
    } finally {
      setIsDeleting(false);
    }
  }

  async function handleView() {
    if (!document) return;
    setError(null);
    setIsViewing(true);
    try {
      const blob = await fetchDocumentFileBlob(loanApplicationId, document.id);
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener,noreferrer");
      // Released after a short delay rather than immediately — revoking
      // right away can race with the new tab still loading the resource.
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (err) {
      setError(getErrorMessage(err, "Could not open this file."));
    } finally {
      setIsViewing(false);
    }
  }

  const canDelete = document && document.status !== "verified";

  return (
    <Card>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-display text-sm font-semibold text-ink">{label}</h3>
          <p className="mt-0.5 text-xs text-muted">{hint}</p>
        </div>
        {document && <DocumentStatusBadge status={document.status} />}
      </div>

      {error && (
        <div className="mt-3">
          <Alert tone="error">{error}</Alert>
        </div>
      )}

      {document ? (
        <div className="mt-4 flex items-center justify-between gap-3 rounded-xl border border-line bg-canvas px-3.5 py-3">
          <div className="flex min-w-0 items-center gap-2.5">
            <FileText className="h-4 w-4 shrink-0 text-muted" aria-hidden="true" />
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-ink">{document.original_filename}</p>
              <p className="text-xs text-muted">
                {formatFileSize(document.file_size_bytes)} · Uploaded{" "}
                {formatDate(document.uploaded_at)}
              </p>
            </div>
          </div>
          <div className="flex shrink-0 gap-2">
            <Button variant="ghost" onClick={handleView} isLoading={isViewing}>
              View
            </Button>
            {canDelete && (
              <Button variant="ghost" onClick={handleDelete} isLoading={isDeleting}>
                <Trash2 className="h-4 w-4" aria-hidden="true" />
              </Button>
            )}
          </div>
        </div>
      ) : (
        <div className="mt-4">
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_MIME_TYPES.join(",")}
            onChange={handleFileSelected}
            className="hidden"
            id={`file-input-${documentType}`}
          />
          <Button
            variant="secondary"
            onClick={() => fileInputRef.current?.click()}
            isLoading={isUploading}
          >
            <Upload className="h-4 w-4" aria-hidden="true" />
            Upload {label.toLowerCase()}
          </Button>
        </div>
      )}

      {document?.status === "rejected" && document.verification_notes && (
        <div className="mt-3">
          <Alert tone="error">Rejected: {document.verification_notes}</Alert>
        </div>
      )}
    </Card>
  );
}