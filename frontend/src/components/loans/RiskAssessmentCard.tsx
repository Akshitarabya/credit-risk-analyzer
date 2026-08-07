import { AlertTriangle, CheckCircle2, HelpCircle } from "lucide-react";

import Card from "@/components/ui/Card";
import type { Recommendation, RiskCategory, RiskFactor } from "@/types/loan";

interface RiskAssessmentCardProps {
  riskScore: number;
  riskCategory: RiskCategory;
  recommendation: Recommendation;
  topRiskFactors: RiskFactor[] | null;
}

const CATEGORY_CONFIG: Record<
  RiskCategory,
  {
    label: string;
    textColor: string;
    bgColor: string;
    ringColor: string;
    Icon: typeof CheckCircle2;
  }
> = {
  low: {
    label: "Low risk",
    textColor: "text-teal",
    bgColor: "bg-teal-soft",
    ringColor: "ring-teal/30",
    Icon: CheckCircle2,
  },
  medium: {
    label: "Medium risk",
    textColor: "text-amber",
    bgColor: "bg-amber-soft",
    ringColor: "ring-amber/30",
    Icon: HelpCircle,
  },
  high: {
    label: "High risk",
    textColor: "text-coral",
    bgColor: "bg-coral-soft",
    ringColor: "ring-coral/30",
    Icon: AlertTriangle,
  },
};

const RECOMMENDATION_LABELS: Record<Recommendation, string> = {
  approved: "Approved",
  review: "Needs manual review",
  reject: "Not approved",
};

const FACTOR_LABELS: Record<string, string> = {
  annual_income: "Annual income",
  existing_debt: "Existing debt",
  credit_history_years: "Credit history length",
  loan_amount: "Loan amount",
  loan_tenure_months: "Loan tenure",
  debt_to_income: "Debt-to-income ratio",
  loan_to_income: "Loan-to-income ratio",
  employment_employed: "Employment status",
  employment_self_employed: "Employment status",
  employment_student: "Employment status",
  employment_unemployed: "Employment status",
  purpose_personal: "Loan purpose",
  purpose_auto: "Loan purpose",
  purpose_education: "Loan purpose",
  purpose_business: "Loan purpose",
  purpose_home: "Loan purpose",
};

export default function RiskAssessmentCard({
  riskScore,
  riskCategory,
  recommendation,
  topRiskFactors,
}: RiskAssessmentCardProps) {
  const config = CATEGORY_CONFIG[riskCategory];
  const Icon = config.Icon;

  return (
    <Card className={`ring-1 ${config.ringColor}`}>
      <div className="flex items-start justify-between">
        <h2 className="font-display text-base font-semibold text-ink">Risk assessment</h2>
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold ${config.bgColor} ${config.textColor}`}
        >
          <Icon className="h-4 w-4" aria-hidden="true" />
          {config.label}
        </span>
      </div>

      <div className="mt-6 flex items-end gap-6">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted">Risk score</p>
          <p className={`font-mono text-5xl font-semibold tabular-nums ${config.textColor}`}>
            {riskScore}
            <span className="text-xl text-muted">/100</span>
          </p>
        </div>
        <div className="pb-1.5">
          <p className="text-xs font-medium uppercase tracking-wide text-muted">Recommendation</p>
          <p className="text-lg font-semibold text-ink">{RECOMMENDATION_LABELS[recommendation]}</p>
        </div>
      </div>

      {/* A simple visual position on the 0-100 continuum — the same
          "ledgerline" idea as the brand mark, now doing real work. */}
      <div className="mt-5 h-2 w-full overflow-hidden rounded-full bg-line">
        <div
          className={`h-full rounded-full ${
            riskCategory === "low" ? "bg-teal" : riskCategory === "medium" ? "bg-amber" : "bg-coral"
          }`}
          style={{ width: `${riskScore}%` }}
        />
      </div>

      {topRiskFactors && topRiskFactors.length > 0 && (
        <div className="mt-6 border-t border-line pt-5">
          <p className="text-xs font-medium uppercase tracking-wide text-muted">
            Key factors considered
          </p>
          <ul className="mt-2.5 flex flex-col gap-2">
            {topRiskFactors.map((factor) => (
              <li key={factor.feature} className="flex items-center gap-2 text-sm text-ink">
                <span
                  className={`h-1.5 w-1.5 shrink-0 rounded-full ${
                    factor.direction === "increases_risk" ? "bg-coral" : "bg-teal"
                  }`}
                />
                {FACTOR_LABELS[factor.feature] ?? factor.feature}
                <span className="text-xs text-muted">
                  ({factor.direction === "increases_risk" ? "increased" : "decreased"} risk)
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
}