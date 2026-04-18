"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { medicinesApi } from "@/lib/api/medicines";
import type { MedicineCreate } from "@/types";

export function useMedicines(memberId: string | undefined) {
  return useQuery({
    queryKey: ["medicines", memberId],
    queryFn: () => medicinesApi.list(memberId!),
    enabled: !!memberId,
    staleTime: 2 * 60 * 1000,
  });
}

export function useActiveMedicines(memberId: string | undefined) {
  return useQuery({
    queryKey: ["medicines-active", memberId],
    queryFn: () => medicinesApi.active(memberId!),
    enabled: !!memberId,
    staleTime: 2 * 60 * 1000,
  });
}

export function useCreateMedicine(memberId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: MedicineCreate) => medicinesApi.create(payload),
    onSuccess: () => {
      toast.success("Medicine added.");
      queryClient.invalidateQueries({ queryKey: ["medicines", memberId] });
      queryClient.invalidateQueries({ queryKey: ["medicines-active", memberId] });
    },
    onError: (e: Error) => toast.error(e.message),
  });
}

export function useToggleMedicine(memberId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => medicinesApi.toggle(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["medicines", memberId] });
      queryClient.invalidateQueries({ queryKey: ["medicines-active", memberId] });
    },
    onError: () => toast.error("Failed to update medicine status."),
  });
}

export function useDeleteMedicine(memberId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => medicinesApi.delete(id),
    onSuccess: () => {
      toast.success("Medicine removed.");
      queryClient.invalidateQueries({ queryKey: ["medicines", memberId] });
      queryClient.invalidateQueries({ queryKey: ["medicines-active", memberId] });
    },
    onError: () => toast.error("Failed to delete medicine."),
  });
}
