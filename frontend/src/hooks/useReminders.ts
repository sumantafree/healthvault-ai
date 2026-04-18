// HealthVault AI — Reminders Hooks (TanStack Query)

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { remindersApi } from "@/lib/api/reminders";
import type { ReminderCreate } from "@/types";

const key = (memberId?: string) => ["reminders", memberId];

export function useReminders(memberId?: string) {
  return useQuery({
    queryKey: key(memberId),
    queryFn: () => remindersApi.list(memberId!).then((r) => r.data),
    enabled: !!memberId,
  });
}

export function useCreateReminder(memberId?: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ReminderCreate) =>
      remindersApi.create(data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: key(memberId) });
      toast.success("Reminder created");
    },
    onError: (e: any) => toast.error(e.message ?? "Failed to create reminder"),
  });
}

export function useToggleReminder(memberId?: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => remindersApi.toggle(id).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: key(memberId) }),
    onError: (e: any) => toast.error(e.message ?? "Failed to toggle reminder"),
  });
}

export function useDeleteReminder(memberId?: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => remindersApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: key(memberId) });
      toast.success("Reminder deleted");
    },
    onError: (e: any) => toast.error(e.message ?? "Failed to delete reminder"),
  });
}
