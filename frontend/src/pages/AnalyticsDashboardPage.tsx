import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { fetchAnalyticsSummary } from "@/api/analytics";
import AppShell from "@/components/layout/AppShell";
import Alert from "@/components/ui/Alert";
import Card from "@/components/ui/Card";
import { getErrorMessage } from "@/utils/errors";
import { formatCurrency, formatDate } from "@/utils/format";
import type { AnalyticsSummary } from "@/types/analytics";
import type { LoanStatus, RiskCategory } from "@/types/loan";

const STATUS_LABELS: Record<LoanStatus, string> = {
  submitted: "Submitted",
  scored: "Scored",
  manual_review: "In review",
  approved: "Approved",
  rejected: "Rejected",
};

// Matches the semantic risk colors already used by RiskAssessmentCard/RiskCategoryBadge.
const RISK_COLORS: Record<RiskCategory, string> = {
  low: "#0E8F7E",
  medium: "#C97F1E",
  high: "#C1473F",
};

const RISK_LABELS: Record<RiskCategory, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
};

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <p className="text-xs font-medium uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-1.5 font-mono text-2xl font-semibold text-ink">{value}</p>
    </Card>
  );
}

export default function AnalyticsDashboardPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalyticsSummary()
      .then(setSummary)
      .catch((err) => setError(getErrorMessage(err, "Could not load analytics.")));
  }, []);

  return (
    <AppShell>
      <div className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-[0.15em] text-teal">
          Portfolio
        </p>
        <h1 className="mt-1.5 text-3xl font-semibold tracking-tight">Analytics</h1>
        <p className="mt-2 text-sm text-muted">
          Loan volume, decisions, and risk distribution across the platform.
        </p>
      </div>

      {error && <Alert tone="error">{error}</Alert>}

      {!summary && !error && (
        <div className="flex justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-line border-t-navy" />
        </div>
      )}

      {summary && summary.total_applications === 0 && (
        <Card className="py-16 text-center">
          <p className="text-sm text-muted">
            No applications have been submitted yet — analytics will appear here once they are.
          </p>
        </Card>
      )}

      {summary && summary.total_applications > 0 && (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatCard label="Total applications" value={String(summary.total_applications)} />
            <StatCard
              label="Approval rate"
              value={summary.approval_rate !== null ? `${Math.round(summary.approval_rate * 100)}%` : "—"}
            />
            <StatCard
              label="Avg. loan amount"
              value={summary.average_loan_amount !== null ? formatCurrency(summary.average_loan_amount) : "—"}
            />
            <StatCard
              label="Avg. risk score"
              value={summary.average_risk_score !== null ? Math.round(summary.average_risk_score).toString() : "—"}
            />
          </div>

          <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card>
              <h2 className="font-display text-base font-semibold text-ink">Applications by status</h2>
              <div className="mt-4 h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={summary.status_counts.map((s) => ({
                      label: STATUS_LABELS[s.status],
                      count: s.count,
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#E3E8EF" vertical={false} />
                    <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="#62697A" />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} stroke="#62697A" />
                    <Tooltip />
                    <Bar dataKey="count" fill="#10213D" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>

            <Card>
              <h2 className="font-display text-base font-semibold text-ink">Risk distribution</h2>
              {summary.risk_category_counts.length === 0 ? (
                <p className="mt-4 text-sm text-muted">No scored applications yet.</p>
              ) : (
                <div className="mt-4 h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={summary.risk_category_counts.map((r) => ({
                          name: RISK_LABELS[r.risk_category],
                          value: r.count,
                          category: r.risk_category,
                        }))}
                        dataKey="value"
                        nameKey="name"
                        outerRadius={90}
                        label={(entry) => `${entry.name}: ${entry.value}`}
                      >
                        {summary.risk_category_counts.map((r) => (
                          <Cell key={r.risk_category} fill={RISK_COLORS[r.risk_category]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              )}
            </Card>

            <Card className="lg:col-span-2">
              <h2 className="font-display text-base font-semibold text-ink">
                Applications received (last 30 days)
              </h2>
              {summary.applications_trend.length === 0 ? (
                <p className="mt-4 text-sm text-muted">No applications in this window yet.</p>
              ) : (
                <div className="mt-4 h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={summary.applications_trend.map((t) => ({
                        date: formatDate(t.date),
                        count: t.count,
                      }))}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#E3E8EF" vertical={false} />
                      <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#62697A" />
                      <YAxis allowDecimals={false} tick={{ fontSize: 12 }} stroke="#62697A" />
                      <Tooltip />
                      <Line type="monotone" dataKey="count" stroke="#0E8F7E" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </Card>
          </div>
        </>
      )}
    </AppShell>
  );
}