import type { LoanPurpose } from "@/types/loan";
import type { EmploymentStatus } from "@/types/applicant";

export const loanPurposeLabels: Record<LoanPurpose, string> = {
  personal: "Personal",
  auto: "Auto",
  education: "Education",
  business: "Business",
  home: "Home",
};

export const employmentStatusLabels: Record<EmploymentStatus, string> = {
  employed: "Employed",
  self_employed: "Self-employed",
  unemployed: "Unemployed",
  student: "Student",
};