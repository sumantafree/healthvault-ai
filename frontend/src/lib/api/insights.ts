import { apiClient } from "./client";
import type { AIInsight } from "@/types";

export const insightsApi = {
  list: (familyMemberId: string) =>
    apiClient
      .get<AIInsight[]>("/insights/", { params: { family_member_id: familyMemberId } })
      .then((r) => r.data),

  latest: (familyMemberId: string) =>
    apiClient
      .get<AIInsight>("/insights/latest", { params: { family_member_id: familyMemberId } })
      .then((r) => r.data),

  forReport: (reportId: string) =>
    apiClient.get<AIInsight>(`/insights/report/${reportId}`).then((r) => r.data),

  reanalyze: (reportId: string) =>
    apiClient.post<{ message: string; status: string }>(`/insights/reanalyze/${reportId}`).then((r) => r.data),
};
