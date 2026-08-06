export type EmploymentStatus = "employed" | "self_employed" | "unemployed" | "student";

export interface ApplicantProfile {
  id: string;
  user_id: string;
  full_name: string;
  date_of_birth: string;
  annual_income: number;
  employment_status: EmploymentStatus;
  existing_debt: number;
  credit_history_years: number;
  created_at: string;
  updated_at: string;
}

export interface ApplicantProfileInput {
  full_name: string;
  date_of_birth: string;
  annual_income: number;
  employment_status: EmploymentStatus;
  existing_debt: number;
  credit_history_years: number;
}