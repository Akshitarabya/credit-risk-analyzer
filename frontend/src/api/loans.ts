import apiClient from "@/api/client";
import type {
  LoanApplication,
  LoanApplicationDetail,
  LoanApplicationSubmission,
  LoanPrediction,
  LoanStatus,
  ReviewDecisionPayload,
  ReviewNotesPayload,
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

export async function fetchLoanApplication(
  id: string
): Promise<LoanApplicationDetail> {
  const { data } = await apiClient.get<LoanApplicationDetail>(
    `/loans/${id}`
  );
  return data;
}

export async function fetchLoanPrediction(
  id: string
): Promise<LoanPrediction> {
  const { data } = await apiClient.get<LoanPrediction>(
    `/loans/${id}/prediction`
  );
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

// --- Module 4: staff review workflow ---

export async function fetchPendingLoanApplications(): Promise<
  LoanApplication[]
> {
  const { data } = await apiClient.get<LoanApplication[]>(
    "/loans/pending"
  );
  return data;
}

export async function submitReviewDecision(
  id: string,
  payload: ReviewDecisionPayload
): Promise<LoanApplication> {
  const { data } = await apiClient.patch<LoanApplication>(
    `/loans/${id}/decision`,
    payload
  );
  return data;
}

export async function submitReviewNotes(
  id: string,
  payload: ReviewNotesPayload
): Promise<LoanApplication> {
  const { data } = await apiClient.patch<LoanApplication>(
    `/loans/${id}/notes`,
    payload
  );
  return data;
}