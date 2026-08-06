import apiClient from "@/api/client";
import type { ApplicantProfile, ApplicantProfileInput } from "@/types/applicant";

export async function fetchMyApplicantProfile(): Promise<ApplicantProfile> {
  const { data } = await apiClient.get<ApplicantProfile>("/applicants/me");
  return data;
}

export async function updateMyApplicantProfile(
  payload: ApplicantProfileInput
): Promise<ApplicantProfile> {
  const { data } = await apiClient.patch<ApplicantProfile>("/applicants/me", payload);
  return data;
}