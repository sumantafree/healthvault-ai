"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { insightsApi } from "@/lib/api/insights";
import { toast } from "sonner";

export function useLatestInsight(memberId: string | undefined) {
  return useQuery({
    queryKey: ["insight-latest", memberId],
    queryFn: () => insightsApi.latest(memberId!),
    enabled: !!memberId,
    staleTime: 5 * 60 * 1000,
    retry: false, // 404 is expected when no reports exist
  });
}

export function useInsights(memberId: string | undefined) {
  return useQuery({
    queryKey: ["insights", memberId],
    queryFn: () => insightsApi.list(memberId!),
    enabled: !!memberId,
    staleTime: 5 * 60 * 1000,
  });
}

export function useReanalyze() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (reportId: string) => insightsApi.reanalyze(reportId),
    onSuccess: (_, reportId) => {
      toast.success("Re-analysis started. This may take a moment.");
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["insights"] });
        queryClient.invalidateQueries({ queryKey: ["insight-latest"] });
        queryClient.invalidateQueries({ queryKey: ["reports"] });
      }, 3000);
    },
    onError: () => toast.error("Failed to start re-analysis."),
  });
}
