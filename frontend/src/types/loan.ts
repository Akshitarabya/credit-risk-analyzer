import type { ApplicantProfile, ApplicantProfileInput } from "@/types/applicant";

export type LoanPurpose = "personal" | "auto" | "education" | "business" | "home";

export type LoanStatus = "submitted" | "scored" | "approved" | "rejected" | "manual_review";

export interface LoanApplication {
  id: string;
  applicant_id: string;
  loan_amount: number;
  loan_purpose: LoanPurpose;
  loan_tenure_months: number;
  status: LoanStatus;
  submitted_at: string;
}

export interface LoanApplicationDetail extends LoanApplication {
  applicant: ApplicantProfile;
}

export interface LoanApplicationSubmission extends ApplicantProfileInput {
  loan_amount: number;
  loan_purpose: LoanPurpose;
  loan_tenure_months: number;
}