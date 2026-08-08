import { useState } from "react";
import { CheckCircle2, Clock, ShieldAlert, XCircle } from "lucide-react";

import { submitReviewDecision, submitReviewNotes } from "@/api/loans";
import Alert from "@/components/ui/Alert";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Textarea from "@/components/ui/Textarea";
import { getErrorMessage } from "@/utils/errors";
import { formatDate } from "@/utils/format";
import type { DecisionAction, LoanApplicationDetail } from "@/types/loan";

interface ReviewPanelProps {
  application: LoanApplicationDetail;
  /** Called after any successful mutation so the parent can refetch the full detail. */
  onUpdated: () => Promise<void> | void;
}

const ACTION_CONFIG: Record<
  DecisionAction,
  {
    label: string;
    confirmLabel: string;
    variant: "primary" | "danger" | "secondary";
    Icon: typeof CheckCircle2;
  }
> = {
  approved: {
    label: "Approve",
    confirmLabel: "Confirm approval",
    variant: "primary",
    Icon: CheckCircle2,
  },
  rejected: {
    label: "Reject",
    confirmLabel: "Confirm rejection",
    variant: "danger",
    Icon: XCircle,
  },
  manual_review: {
    label: "Send to manual review",
    confirmLabel: "Confirm send to review",
    variant: "secondary",
    Icon: ShieldAlert,
  },
};

// Mirrors backend review_service.ALLOWED_TRANSITIONS exactly.
const AVAILABLE_ACTIONS: Record<string, DecisionAction[]> = {
  scored: ["approved", "rejected", "manual_review"],
  manual_review: ["approved", "rejected"],
};

export default function ReviewPanel({
  application,
  onUpdated,
}: ReviewPanelProps) {
  const [notes, setNotes] = useState(application.review_notes ?? "");
  const [pendingAction, setPendingAction] =
    useState<DecisionAction | null>(null);

  const [isSubmittingDecision, setIsSubmittingDecision] = useState(false);
  const [isSavingNotes, setIsSavingNotes] = useState(false);

  const [decisionError, setDecisionError] = useState<string | null>(null);
  const [notesError, setNotesError] = useState<string | null>(null);
  const [notesSaved, setNotesSaved] = useState(false);

  const isFinal = application.final_decision !== null;
  const availableActions =
    AVAILABLE_ACTIONS[application.status] ?? [];
  const notYetScored = application.status === "submitted";

  async function handleConfirmDecision(action: DecisionAction) {
    setDecisionError(null);
    setIsSubmittingDecision(true);

    try {
      await submitReviewDecision(application.id, {
        decision: action,
        notes: notes.trim() ? notes.trim() : undefined,
      });

      setPendingAction(null);
      await onUpdated();
    } catch (err) {
      setDecisionError(
        getErrorMessage(err, "Could not record this decision.")
      );
    } finally {
      setIsSubmittingDecision(false);
    }
  }

  async function handleSaveNotes() {
    setNotesError(null);
    setNotesSaved(false);
    setIsSavingNotes(true);

    try {
      await submitReviewNotes(application.id, {
        notes: notes.trim(),
      });

      setNotesSaved(true);
      await onUpdated();
    } catch (err) {
      setNotesError(
        getErrorMessage(err, "Could not save notes.")
      );
    } finally {
      setIsSavingNotes(false);
    }
  }

  return (
    <Card className="mt-6">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-base font-semibold text-ink">
          Staff review
        </h2>

        {isFinal && (
          <Badge
            tone={
              application.final_decision === "approved"
                ? "teal"
                : "coral"
            }
          >
            Final decision:{" "}
            {application.final_decision === "approved"
              ? "Approved"
              : "Rejected"}
          </Badge>
        )}
      </div>

      {(application.reviewer_name || application.reviewed_at) && (
        <div className="mt-3 flex items-center gap-1.5 text-sm text-muted">
          <Clock
            className="h-3.5 w-3.5"
            aria-hidden="true"
          />

          {application.reviewer_name && (
            <span>
              Reviewed by {application.reviewer_name}
            </span>
          )}

          {application.reviewer_name &&
            application.reviewed_at && <span>·</span>}

          {application.reviewed_at && (
            <span>{formatDate(application.reviewed_at)}</span>
          )}
        </div>
      )}

      {notYetScored && (
        <p className="mt-4 text-sm text-muted">
          This application hasn't been scored yet, so it can't
          be reviewed.
        </p>
      )}

      {!notYetScored && (
        <>
          <div className="mt-5">
            <Textarea
              label="Internal review notes"
              value={notes}
              onChange={(e) => {
                setNotes(e.target.value);
                setNotesSaved(false);
              }}
              disabled={
                isFinal ||
                isSubmittingDecision ||
                isSavingNotes
              }
              rows={4}
              placeholder="Notes for other reviewers — not shown to the applicant's public status page."
              hint={
                isFinal
                  ? "This application has a final decision and can no longer be edited."
                  : undefined
              }
            />

            {notesError && (
              <div className="mt-2">
                <Alert tone="error">{notesError}</Alert>
              </div>
            )}

            {notesSaved && !notesError && (
              <div className="mt-2">
                <Alert tone="success">
                  Notes saved.
                </Alert>
              </div>
            )}

            {!isFinal && (
              <div className="mt-3">
                <Button
                  variant="secondary"
                  onClick={handleSaveNotes}
                  isLoading={isSavingNotes}
                  disabled={isSubmittingDecision}
                >
                  Save notes
                </Button>
              </div>
            )}
          </div>

          {decisionError && (
            <div className="mt-5">
              <Alert tone="error">{decisionError}</Alert>
            </div>
          )}

          {!isFinal && availableActions.length > 0 && (
            <div className="mt-5 border-t border-line pt-5">
              {pendingAction === null ? (
                <div className="flex flex-wrap gap-2.5">
                  {availableActions.map((action) => {
                    const config = ACTION_CONFIG[action];
                    const Icon = config.Icon;

                    return (
                      <Button
                        key={action}
                        variant={config.variant}
                        onClick={() =>
                          setPendingAction(action)
                        }
                        disabled={
                          isSubmittingDecision ||
                          isSavingNotes
                        }
                      >
                        <Icon
                          className="h-4 w-4"
                          aria-hidden="true"
                        />
                        {config.label}
                      </Button>
                    );
                  })}
                </div>
              ) : (
                <div className="rounded-xl border border-line bg-canvas px-4 py-4">
                  <p className="text-sm font-medium text-ink">
                    {
                      ACTION_CONFIG[pendingAction]
                        .confirmLabel
                    }
                    ? This will update the application's
                    status
                    {notes.trim()
                      ? " and save your notes"
                      : ""}
                    .
                  </p>

                  <div className="mt-3 flex gap-2.5">
                    <Button
                      variant={
                        ACTION_CONFIG[pendingAction].variant
                      }
                      onClick={() =>
                        handleConfirmDecision(pendingAction)
                      }
                      isLoading={isSubmittingDecision}
                    >
                      {
                        ACTION_CONFIG[pendingAction]
                          .confirmLabel
                      }
                    </Button>

                    <Button
                      variant="ghost"
                      onClick={() =>
                        setPendingAction(null)
                      }
                      disabled={isSubmittingDecision}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </Card>
  );
}