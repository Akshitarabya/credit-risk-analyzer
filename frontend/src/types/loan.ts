import type { ApplicantProfile, ApplicantProfileInput } from "@/types/applicant";

export type LoanPurpose = "personal" | "auto" | "education" | "business" | "home";

export type LoanStatus = "submitted" | "scored" | "approved" | "rejected" | "manual_review";

export type RiskCategory = "low" | "medium" | "high";

export type Recommendation = "approved" | "review" | "reject";

export interface RiskFactor {
  feature: string;
  impact: number;
  direction: "increases_risk" | "decreases_risk";
}

export interface LoanApplication {
  id: string;
  applicant_id: string;
  loan_amount: number;
  loan_purpose: LoanPurpose;
  loan_tenure_months: number;
  status: LoanStatus;
  submitted_at: string;
  risk_score: number | null;
  risk_category: RiskCategory | null;
  recommendation: Recommendation | null;
  prediction_timestamp: string | null;
  model_version: string | null;
  top_risk_factors: RiskFactor[] | null;
}

export interface LoanApplicationDetail extends LoanApplication {
  applicant: ApplicantProfile;
}

export interface LoanApplicationSubmission extends ApplicantProfileInput {
  loan_amount: number;
  loan_purpose: LoanPurpose;
  loan_tenure_months: number;
}

export interface LoanPrediction {
  loan_application_id: string;
  risk_score: number;
  risk_category: RiskCategory;
  recommendation: Recommendation;
  prediction_timestamp: string;
  model_version: string;
  top_risk_factors: RiskFactor[];
}