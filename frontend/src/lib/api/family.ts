import { apiClient } from "./client";
import type { FamilyMember, FamilyMemberCreate } from "@/types";

export const familyApi = {
  list: () =>
    apiClient.get<FamilyMember[]>("/family/").then((r) => r.data),

  get: (id: string) =>
    apiClient.get<FamilyMember>(`/family/${id}`).then((r) => r.data),

  create: (payload: FamilyMemberCreate) =>
    apiClient.post<FamilyMember>("/family/", payload).then((r) => r.data),

  update: (id: string, payload: Partial<FamilyMemberCreate>) =>
    apiClient.patch<FamilyMember>(`/family/${id}`, payload).then((r) => r.data),

  delete: (id: string) =>
    apiClient.delete(`/family/${id}`),
};
