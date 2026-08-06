import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { fetchAllLoanApplications } from "@/api/loans";
import AppShell from "@/components/layout/AppShell";
import LoanStatusBadge from "@/components/loans/LoanStatusBadge";
import Alert from "@/components/ui/Alert";
import Card from "@/components/ui/Card";
import { getErrorMessage } from "@/utils/errors";
import { formatCurrency, formatDate } from "@/utils/format";
import { loanPurposeLabels } from "@/utils/labels";
import type { LoanApplication, LoanStatus } from "@/types/loan";

const STATUS_FILTERS: { value: LoanStatus | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "submitted", label: "Submitted" },
  { value: "scored", label: "Scored" },
  { value: "manual_review", label: "In review" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
];

export default function StaffDashboardPage() {
  const [applications, setApplications] = useState<LoanApplication[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<LoanStatus | "all">("all");

  useEffect(() => {
    setApplications(null);
    fetchAllLoanApplications(statusFilter === "all" ? undefined : statusFilter)
      .then(setApplications)
      .catch((err) => setError(getErrorMessage(err, "Could not load applications.")));
  }, [statusFilter]);

  return (
    <AppShell>
      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-[0.15em] text-teal">
          Underwriting
        </p>
        <h1 className="mt-1.5 text-3xl font-semibold tracking-tight">Application queue</h1>
        <p className="mt-2 text-sm text-muted">
          Every loan application submitted across the platform.
        </p>
      </div>

      <div className="mb-5 flex flex-wrap gap-2">
        {STATUS_FILTERS.map((filter) => (
          <button
            key={filter.value}
            onClick={() => setStatusFilter(filter.value)}
            className={`rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors
              focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy
              ${
                statusFilter === filter.value
                  ? "bg-navy text-white"
                  : "bg-white text-muted border border-line hover:border-navy/30"
              }`}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {error && <Alert tone="error">{error}</Alert>}

      {applications === null && !error && (
        <div className="flex justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-line border-t-navy" />
        </div>
      )}

      {applications !== null && applications.length === 0 && (
        <Card className="py-16 text-center">
          <p className="text-sm text-muted">No applications match this filter.</p>
        </Card>
      )}

      {applications !== null && applications.length > 0 && (
        <Card className="overflow-hidden p-0">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-line bg-canvas">
              <tr>
                <th className="px-5 py-3 font-medium text-muted">Amount</th>
                <th className="px-5 py-3 font-medium text-muted">Purpose</th>
                <th className="px-5 py-3 font-medium text-muted">Tenure</th>
                <th className="px-5 py-3 font-medium text-muted">Submitted</th>
                <th className="px-5 py-3 font-medium text-muted">Status</th>
              </tr>
            </thead>
            <tbody>
              {applications.map((application) => (
                <tr key={application.id} className="border-b border-line last:border-0">
                  <td className="px-5 py-3">
                    <Link
                      to={`/applications/${application.id}`}
                      className="font-mono font-semibold text-navy hover:underline"
                    >
                      {formatCurrency(application.loan_amount)}
                    </Link>
                  </td>
                  <td className="px-5 py-3 text-ink">
                    {loanPurposeLabels[application.loan_purpose]}
                  </td>
                  <td className="px-5 py-3 text-ink">{application.loan_tenure_months} mo</td>
                  <td className="px-5 py-3 text-muted">{formatDate(application.submitted_at)}</td>
                  <td className="px-5 py-3">
                    <LoanStatusBadge status={application.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </AppShell>
  );
}