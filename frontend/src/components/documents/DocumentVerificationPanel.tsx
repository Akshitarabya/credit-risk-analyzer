import { useEffect, useState } from "react";
import { CheckCircle2, ChevronDown, ChevronUp, XCircle } from "lucide-react";

import { fetchDocument, fetchDocumentFileBlob, verifyDocument } from "@/api/documents";
import DocumentStatusBadge from "@/components/documents/DocumentStatusBadge";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import Textarea from "@/components/ui/Textarea";
import { getErrorMessage } from "@/utils/errors";
import { formatDate } from "@/utils/format";
import type { DocumentDetail, DocumentSummary } from "@/types/document";

interface DocumentVerificationPanelProps {
  loanApplicationId: string;
  document: DocumentSummary;
  label: string;
  /** Whether the parent loan already has a final decision — blocks further review actions. */
  loanIsFinal: boolean;
  onChanged: () => Promise<void> | void;
}

export default function DocumentVerificationPanel({
  loanApplicationId,
  document,
  label,
  loanIsFinal,
  onChanged,
}: DocumentVerificationPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [detail, setDetail] = useState<DocumentDetail | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isViewing, setIsViewing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isExpanded || detail) return;
    setIsLoadingDetail(true);
    fetchDocument(loanApplicationId, document.id)
      .then(setDetail)
      .catch((err) => setError(getErrorMessage(err, "Could not load document details.")))
      .finally(() => setIsLoadingDetail(false));
  }, [isExpanded, detail, loanApplicationId, document.id]);

  const canReview = !loanIsFinal && (document.status === "uploaded" || document.status === "ocr_failed");

  async function handleVerify(newStatus: "verified" | "rejected") {
    setError(null);
    setIsSubmitting(true);
    try {
      await verifyDocument(loanApplicationId, document.id, {
        status: newStatus,
        notes: notes.trim() ? notes.trim() : undefined,
      });
      await onChanged();
    } catch (err) {
      setError(getErrorMessage(err, "Could not record this decision."));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleView() {
    setError(null);
    setIsViewing(true);
    try {
      const blob = await fetchDocumentFileBlob(loanApplicationId, document.id);
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener,noreferrer");
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (err) {
      setError(getErrorMessage(err, "Could not open this file."));
    } finally {
      setIsViewing(false);
    }
  }

  return (
    <div className="rounded-xl border border-line">
      <button
        onClick={() => setIsExpanded((prev) => !prev)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left
          focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy"
      >
        <div className="flex items-center gap-2.5">
          <span className="text-sm font-medium text-ink">{label}</span>
          <DocumentStatusBadge status={document.status} />
        </div>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4 text-muted" aria-hidden="true" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted" aria-hidden="true" />
        )}
      </button>

      {isExpanded && (
        <div className="border-t border-line px-4 py-4">
          {error && (
            <div className="mb-3">
              <Alert tone="error">{error}</Alert>
            </div>
          )}

          <div className="flex items-center justify-between text-xs text-muted">
            <span>
              {document.original_filename} · Uploaded {formatDate(document.uploaded_at)}
            </span>
            <Button variant="ghost" onClick={handleView} isLoading={isViewing}>
              View file
            </Button>
          </div>

          {isLoadingDetail && (
            <div className="mt-3 flex justify-center py-4">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-line border-t-navy" />
            </div>
          )}

          {detail?.ocr_error_message && (
            <div className="mt-3">
              <Alert tone="error">OCR failed: {detail.ocr_error_message}</Alert>
            </div>
          )}

          {detail?.ocr_raw_text && (
            <div className="mt-3">
              <p className="text-xs font-medium uppercase tracking-wide text-muted">
                Extracted text
              </p>
              <p className="mt-1 max-h-32 overflow-y-auto rounded-lg bg-canvas p-3 font-mono text-xs text-ink">
                {detail.ocr_raw_text}
              </p>
              {detail.ocr_confidence !== null && (
                <p className="mt-1 text-xs text-muted">
                  OCR confidence: {Math.round((detail.ocr_confidence ?? 0) * 100)}%
                </p>
              )}
            </div>
          )}

          {document.status === "verified" || document.status === "rejected" ? (
            <div className="mt-3 text-xs text-muted">
              {document.status === "verified" ? "Verified" : "Rejected"} by{" "}
              {document.verifier_name ?? "a staff member"}
              {document.verified_at && ` on ${formatDate(document.verified_at)}`}
              {document.verification_notes && ` — "${document.verification_notes}"`}
            </div>
          ) : (
            canReview && (
              <div className="mt-4 border-t border-line pt-4">
                <Textarea
                  label="Notes (optional)"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  disabled={isSubmitting}
                  rows={2}
                  placeholder="Reason for rejection, or any note for the record."
                />
                <div className="mt-3 flex gap-2.5">
                  <Button
                    variant="primary"
                    onClick={() => handleVerify("verified")}
                    isLoading={isSubmitting}
                  >
                    <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                    Verify
                  </Button>
                  <Button
                    variant="danger"
                    onClick={() => handleVerify("rejected")}
                    disabled={isSubmitting}
                  >
                    <XCircle className="h-4 w-4" aria-hidden="true" />
                    Reject
                  </Button>
                </div>
              </div>
            )
          )}

          {loanIsFinal && document.status !== "verified" && document.status !== "rejected" && (
            <p className="mt-3 text-xs text-muted">
              This loan already has a final decision, so this document can no longer be reviewed.
            </p>
          )}
        </div>
      )}
    </div>
  );
}