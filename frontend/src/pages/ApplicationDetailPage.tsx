import { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { fetchLoanApplication } from "@/api/loans";
import { useAuth } from "@/auth/AuthContext";
import AppShell from "@/components/layout/AppShell";
import LoanStatusBadge from "@/components/loans/LoanStatusBadge";
import Alert from "@/components/ui/Alert";
import Card from "@/components/ui/Card";
import { getErrorMessage } from "@/utils/errors";
import { formatCurrency, formatDate } from "@/utils/format";
import { employmentStatusLabels, loanPurposeLabels } from "@/utils/labels";
import type { LoanApplicationDetail } from "@/types/loan";

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

  useEffect(() => {
    if (!id) return;
    fetchLoanApplication(id)
      .then(setApplication)
      .catch((err) =>
        setError(getErrorMessage(err, "Could not load this application."))
      );
  }, [id]);

  const backLink = user?.role === "applicant" ? "/applications" : "/staff/applications";
  const backLabel = user?.role === "applicant" ? "Back to your applications" : "Back to queue";

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

            {application.status === "submitted" && (
              <div className="mt-6 rounded-xl border border-dashed border-line bg-canvas px-4 py-6 text-center">
                <p className="text-sm text-muted">
                  This application hasn't been scored yet — risk scoring and a decision arrive
                  in the next build phase.
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}