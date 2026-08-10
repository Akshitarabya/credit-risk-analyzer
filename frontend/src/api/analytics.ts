import apiClient from "@/api/client";
import type { AnalyticsSummary } from "@/types/analytics";

export async function fetchAnalyticsSummary(): Promise<AnalyticsSummary> {
  const { data } = await apiClient.get<AnalyticsSummary>("/analytics/summary");
  return data;
}