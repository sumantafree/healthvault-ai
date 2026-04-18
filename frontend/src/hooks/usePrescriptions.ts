"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { prescriptionsApi } from "@/lib/api/prescriptions";

export function usePrescriptions(memberId: string | undefined) {
  return useQuery({
    queryKey: ["prescriptions", memberId],
    queryFn: () => prescriptionsApi.list(memberId!),
    enabled: !!memberId,
    staleTime: 2 * 60 * 1000,
  });
}

export function useDeletePrescription(memberId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => prescriptionsApi.delete(id),
    onSuccess: () => {
      toast.success("Prescription deleted.");
      queryClient.invalidateQueries({ queryKey: ["prescriptions", memberId] });
      queryClient.invalidateQueries({ queryKey: ["medicines", memberId] });
    },
    onError: () => toast.error("Failed to delete prescription."),
  });
}

export function useReprocessPrescription(memberId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => prescriptionsApi.reprocess(id),
    onSuccess: () => {
      toast.success("Re-processing started.");
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["prescriptions", memberId] });
        queryClient.invalidateQueries({ queryKey: ["medicines", memberId] });
      }, 3000);
    },
    onError: () => toast.error("Failed to start re-processing."),
  });
}
