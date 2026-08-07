import apiClient from "@/api/client";
import type {
  LoanApplication,
  LoanApplicationDetail,
  LoanApplicationSubmission,
  LoanPrediction,
  LoanStatus,
} from "@/types/loan";

export async function submitLoanApplication(
  payload: LoanApplicationSubmission
): Promise<LoanApplication> {
  const { data } = await apiClient.post<LoanApplication>("/loans", payload);
  return data;
}

export async function fetchMyLoanApplications(): Promise<LoanApplication[]> {
  const { data } = await apiClient.get<LoanApplication[]>("/loans/me");
  return data;
}

export async function fetchLoanApplication(id: string): Promise<LoanApplicationDetail> {
  const { data } = await apiClient.get<LoanApplicationDetail>(`/loans/${id}`);
  return data;
}

export async function fetchLoanPrediction(id: string): Promise<LoanPrediction> {
  const { data } = await apiClient.get<LoanPrediction>(`/loans/${id}/prediction`);
  return data;
}

export async function fetchAllLoanApplications(
  statusFilter?: LoanStatus
): Promise<LoanApplication[]> {
  const { data } = await apiClient.get<LoanApplication[]>("/loans", {
    params: statusFilter ? { status: statusFilter } : undefined,
  });
  return data;
}