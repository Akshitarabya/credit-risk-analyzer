import { useEffect, useState } from "react";
import { FilePlus2 } from "lucide-react";
import { Link } from "react-router-dom";

import { fetchMyLoanApplications } from "@/api/loans";
import AppShell from "@/components/layout/AppShell";
import LoanStatusBadge from "@/components/loans/LoanStatusBadge";
import Alert from "@/components/ui/Alert";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import { getErrorMessage } from "@/utils/errors";
import { formatCurrency, formatDate } from "@/utils/format";
import { loanPurposeLabels } from "@/utils/labels";
import type { LoanApplication } from "@/types/loan";

export default function ApplicationStatusPage() {
  const [applications, setApplications] = useState<LoanApplication[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMyLoanApplications()
      .then(setApplications)
      .catch((err) => setError(getErrorMessage(err, "Could not load your applications.")));
  }, []);

  return (
    <AppShell>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.15em] text-teal">
            Your applications
          </p>
          <h1 className="mt-1.5 text-3xl font-semibold tracking-tight">Application status</h1>
        </div>
        <Link to="/apply">
          <Button>
            <FilePlus2 className="h-4 w-4" aria-hidden="true" />
            New application
          </Button>
        </Link>
      </div>

      {error && <Alert tone="error">{error}</Alert>}

      {applications === null && !error && (
        <div className="flex justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-line border-t-navy" />
        </div>
      )}

      {applications !== null && applications.length === 0 && (
        <Card className="flex flex-col items-center gap-3 py-16 text-center">
          <FilePlus2 className="h-8 w-8 text-muted" aria-hidden="true" />
          <div>
            <p className="font-display text-lg font-semibold text-ink">No applications yet</p>
            <p className="mt-1 text-sm text-muted">
              Once you apply for a loan, you'll be able to track its status here.
            </p>
          </div>
          <Link to="/apply">
            <Button className="mt-2">Apply for a loan</Button>
          </Link>
        </Card>
      )}

      {applications !== null && applications.length > 0 && (
        <div className="flex flex-col gap-3">
          {applications.map((application) => (
            <Link key={application.id} to={`/applications/${application.id}`}>
              <Card className="flex items-center justify-between transition-shadow hover:shadow-card-hover">
                <div>
                  <p className="font-display text-lg font-semibold text-ink">
                    {formatCurrency(application.loan_amount)}
                  </p>
                  <p className="mt-0.5 text-sm text-muted">
                    {loanPurposeLabels[application.loan_purpose]} · {application.loan_tenure_months}{" "}
                    months · Submitted {formatDate(application.submitted_at)}
                  </p>
                </div>
                <LoanStatusBadge status={application.status} />
              </Card>
            </Link>
          ))}
        </div>
      )}
    </AppShell>
  );
}