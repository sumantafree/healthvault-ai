// HealthVault AI — Reminders API Client

import type { Reminder, ReminderCreate } from "@/types";
import { apiClient } from "./client";

export const remindersApi = {
  list: (familyMemberId: string, activeOnly = false) =>
    apiClient.get<Reminder[]>("/reminders/", {
      params: { family_member_id: familyMemberId, active_only: activeOnly },
    }),

  create: (data: ReminderCreate) =>
    apiClient.post<Reminder>("/reminders/", data),

  update: (
    id: string,
    data: Partial<Pick<ReminderCreate, "title" | "message" | "reminder_time" | "frequency" | "whatsapp_number">> & {
      is_active?: boolean;
    }
  ) => apiClient.patch<Reminder>(`/reminders/${id}`, data),

  toggle: (id: string) =>
    apiClient.patch<Reminder>(`/reminders/${id}/toggle`),

  delete: (id: string) =>
    apiClient.delete(`/reminders/${id}`),

  getLogs: (id: string) =>
    apiClient.get<
      {
        id: string;
        channel: string;
        recipient: string | null;
        status: string;
        sent_at: string | null;
        provider_response: Record<string, unknown> | null;
      }[]
    >(`/reminders/${id}/logs`),
};
