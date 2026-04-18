import { apiClient } from "./client";
import type { HealthReport, HealthReportList } from "@/types";

export const reportsApi = {
  list: (familyMemberId: string, page = 1) =>
    apiClient
      .get<HealthReportList>("/reports/", { params: { family_member_id: familyMemberId, page } })
      .then((r) => r.data),

  get: (id: string) =>
    apiClient.get<HealthReport>(`/reports/${id}`).then((r) => r.data),

  upload: (formData: FormData) =>
    apiClient
      .post<HealthReport>("/reports/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data),

  delete: (id: string) =>
    apiClient.delete(`/reports/${id}`),
};
