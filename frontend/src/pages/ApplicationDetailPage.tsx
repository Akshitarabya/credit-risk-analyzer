import { useCallback, useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { fetchDocuments } from "@/api/documents";
import { fetchLoanApplication } from "@/api/loans";
import { useAuth } from "@/auth/AuthContext";
import AppShell from "@/components/layout/AppShell";
import DocumentUploadCard from "@/components/documents/DocumentUploadCard";
import DocumentVerificationPanel from "@/components/documents/DocumentVerificationPanel";
import LoanStatusBadge from "@/components/loans/LoanStatusBadge";
import ReviewPanel from "@/components/loans/ReviewPanel";
import RiskAssessmentCard from "@/components/loans/RiskAssessmentCard";
import Alert from "@/components/ui/Alert";
import Card from "@/components/ui/Card";
import { getErrorMessage } from "@/utils/errors";
import { formatCurrency, formatDate } from "@/utils/format";
import { employmentStatusLabels, loanPurposeLabels } from "@/utils/labels";
import type { LoanApplicationDetail } from "@/types/loan";
import type { DocumentSummary, DocumentType } from "@/types/document";

const REQUIRED_DOCUMENT_TYPES: { type: DocumentType; label: string; hint: string }[] = [
  { type: "id_proof", label: "ID proof", hint: "A government-issued photo ID." },
  { type: "income_proof", label: "Income proof", hint: "A recent pay stub or offer letter." },
  { type: "bank_statement", label: "Bank statement", hint: "Your most recent monthly statement." },
];

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-0.5 text-sm font-semibold text-ink">{value}</p>
    </div>
  );
}

export default function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [application, setApplication] = useState<LoanApplicationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentSummary[] | null>(null);
  const [documentsError, setDocumentsError] = useState<string | null>(null);

  const loadApplication = useCallback(async () => {
    if (!id) return;
    try {
      const data = await fetchLoanApplication(id);
      setApplication(data);
      setError(null);
    } catch (err) {
      setError(getErrorMessage(err, "Could not load this application."));
    }
  }, [id]);

  const loadDocuments = useCallback(async () => {
    if (!id) return;
    try {
      const data = await fetchDocuments(id);
      setDocuments(data);
      setDocumentsError(null);
    } catch (err) {
      setDocumentsError(getErrorMessage(err, "Could not load documents."));
    }
  }, [id]);

  useEffect(() => {
    loadApplication();
    loadDocuments();
  }, [loadApplication, loadDocuments]);

  const isStaff = user?.role === "staff" || user?.role === "admin";
  const isApplicant = user?.role === "applicant";
  const backLink = user?.role === "applicant" ? "/applications" : "/staff/applications";
  const backLabel = user?.role === "applicant" ? "Back to your applications" : "Back to queue";
  const loanIsFinal = application?.final_decision != null;


  return (
    <AppShell>
      <div className="mx-auto max-w-2xl">
        <Link
          to={backLink}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-muted transition-colors hover:text-navy"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          {backLabel}
        </Link>

        {error && (
          <div className="mt-6">
            <Alert tone="error">{error}</Alert>
          </div>
        )}

        {!application && !error && (
          <div className="flex justify-center py-16">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-line border-t-navy" />
          </div>
        )}

        {application && (
          <>
            <div className="mt-6 flex items-start justify-between">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.15em] text-teal">
                  Application
                </p>
                <h1 className="mt-1.5 text-3xl font-semibold tracking-tight">
                  {formatCurrency(application.loan_amount)}
                </h1>
                <p className="mt-1 text-sm text-muted">
                  Submitted {formatDate(application.submitted_at)}
                </p>
              </div>
              <LoanStatusBadge status={application.status} />
            </div>

            <Card className="mt-8">
              <h2 className="font-display text-base font-semibold text-ink">Loan details</h2>
              <div className="mt-5 grid grid-cols-2 gap-5 sm:grid-cols-3">
                <Field label="Amount" value={formatCurrency(application.loan_amount)} />
                <Field label="Purpose" value={loanPurposeLabels[application.loan_purpose]} />
                <Field label="Tenure" value={`${application.loan_tenure_months} months`} />
              </div>
            </Card>

            <div className="mt-6">
              <h2 className="font-display text-base font-semibold text-ink">Documents</h2>

              {documentsError && (
                <div className="mt-3">
                  <Alert tone="error">{documentsError}</Alert>
                </div>
              )}

              {documents === null && !documentsError && (
                <div className="mt-3 flex justify-center py-6">
                  <div className="h-6 w-6 animate-spin rounded-full border-2 border-line border-t-navy" />
                </div>
              )}

              {documents !== null && isApplicant && (
                <div className="mt-3 flex flex-col gap-3">
                  {REQUIRED_DOCUMENT_TYPES.map(({ type, label, hint }) => (
                    <DocumentUploadCard
                      key={type}
                      loanApplicationId={application.id}
                      documentType={type}
                      label={label}
                      hint={hint}
                      document={documents.find((doc) => doc.document_type === type) ?? null}
                      onChanged={loadDocuments}
                    />
                  ))}
                </div>
              )}

              {documents !== null && isStaff && (
                <div className="mt-3 flex flex-col gap-2.5">
                  {documents.length === 0 ? (
                    <Card className="py-8 text-center">
                      <p className="text-sm text-muted">No documents uploaded yet.</p>
                    </Card>
                  ) : (
                    documents.map((document) => {
                      const typeConfig = REQUIRED_DOCUMENT_TYPES.find(
                        (t) => t.type === document.document_type
                      );
                      return (
                        <DocumentVerificationPanel
                          key={document.id}
                          loanApplicationId={application.id}
                          document={document}
                          label={typeConfig?.label ?? document.document_type}
                          loanIsFinal={loanIsFinal}
                          onChanged={loadDocuments}
                        />
                      );
                    })
                  )}
                </div>
              )}
            </div>

            {application.risk_score !== null &&
              application.risk_category !== null &&
              application.recommendation !== null && (
                <div className="mt-6">
                  <RiskAssessmentCard
                    riskScore={application.risk_score}
                    riskCategory={application.risk_category}
                    recommendation={application.recommendation}
                    topRiskFactors={application.top_risk_factors}
                  />
                </div>
              )}

            {/* Staff review actions — never rendered for applicants, even
                though the current API response includes reviewer_name /
                review_notes for any viewer with access to this application.
                Masking that server-side (so applicants truly cannot see
                internal staff notes in the network response) is a backend
                change out of scope for this step and is flagged separately. */}
            {isStaff && <ReviewPanel application={application} onUpdated={loadApplication} />}

            <Card className="mt-6">
              <h2 className="font-display text-base font-semibold text-ink">
                Applicant profile
              </h2>
              <div className="mt-5 grid grid-cols-2 gap-5 sm:grid-cols-3">
                <Field label="Full name" value={application.applicant.full_name} />
                <Field label="Date of birth" value={formatDate(application.applicant.date_of_birth)} />
                <Field
                  label="Employment"
                  value={employmentStatusLabels[application.applicant.employment_status]}
                />
                <Field
                  label="Annual income"
                  value={formatCurrency(application.applicant.annual_income)}
                />
                <Field
                  label="Existing debt"
                  value={formatCurrency(application.applicant.existing_debt)}
                />
                <Field
                  label="Credit history"
                  value={`${application.applicant.credit_history_years} years`}
                />
              </div>
            </Card>

            {application.risk_score === null && (
              <div className="mt-6 rounded-xl border border-dashed border-line bg-canvas px-4 py-6 text-center">
                <p className="text-sm text-muted">
                  This application hasn't been scored yet.
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}