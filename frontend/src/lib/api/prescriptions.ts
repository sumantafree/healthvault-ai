import { apiClient } from "./client";
import type { Prescription } from "@/types";

export const prescriptionsApi = {
  list: (familyMemberId: string) =>
    apiClient
      .get<Prescription[]>("/prescriptions/", { params: { family_member_id: familyMemberId } })
      .then((r) => r.data),

  get: (id: string) =>
    apiClient.get<Prescription>(`/prescriptions/${id}`).then((r) => r.data),

  upload: (formData: FormData) =>
    apiClient
      .post<Prescription>("/prescriptions/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data),

  reprocess: (id: string) =>
    apiClient.post<{ message: string }>(`/prescriptions/${id}/reprocess`).then((r) => r.data),

  delete: (id: string) =>
    apiClient.delete(`/prescriptions/${id}`),
};
