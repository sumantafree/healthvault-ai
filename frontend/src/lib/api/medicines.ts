import { apiClient } from "./client";
import type { Medicine, MedicineCreate } from "@/types";

export const medicinesApi = {
  list: (familyMemberId: string, activeOnly = false) =>
    apiClient
      .get<Medicine[]>("/medicines/", { params: { family_member_id: familyMemberId, active_only: activeOnly } })
      .then((r) => r.data),

  active: (familyMemberId: string) =>
    apiClient
      .get<Medicine[]>("/medicines/active", { params: { family_member_id: familyMemberId } })
      .then((r) => r.data),

  get: (id: string) =>
    apiClient.get<Medicine>(`/medicines/${id}`).then((r) => r.data),

  create: (payload: MedicineCreate) =>
    apiClient.post<Medicine>("/medicines/", payload).then((r) => r.data),

  update: (id: string, payload: Partial<MedicineCreate>) =>
    apiClient.patch<Medicine>(`/medicines/${id}`, payload).then((r) => r.data),

  toggle: (id: string) =>
    apiClient.patch<Medicine>(`/medicines/${id}/toggle`).then((r) => r.data),

  delete: (id: string) =>
    apiClient.delete(`/medicines/${id}`),
};
