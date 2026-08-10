import type { LoanStatus, RiskCategory } from "@/types/loan";

export interface StatusCount {
  status: LoanStatus;
  count: number;
}

export interface RiskCategoryCount {
  risk_category: RiskCategory;
  count: number;
}

export interface TrendPoint {
  date: string;
  count: number;
}

export interface AnalyticsSummary {
  total_applications: number;
  status_counts: StatusCount[];
  risk_category_counts: RiskCategoryCount[];
  average_loan_amount: number | null;
  average_risk_score: number | null;
  approved_count: number;
  rejected_count: number;
  approval_rate: number | null;
  applications_trend: TrendPoint[];
}