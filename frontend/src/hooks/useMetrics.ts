"use client";
import { useQuery } from "@tanstack/react-query";
import { metricsApi } from "@/lib/api/metrics";
import { computeHealthScore } from "@/lib/utils";

export function useMetrics(memberId: string | undefined) {
  const listQuery = useQuery({
    queryKey: ["metrics", memberId],
    queryFn: () => metricsApi.list(memberId!),
    enabled: !!memberId,
    staleTime: 2 * 60 * 1000,
  });

  const abnormalQuery = useQuery({
    queryKey: ["metrics-abnormal", memberId],
    queryFn: () => metricsApi.abnormal(memberId!),
    enabled: !!memberId,
    staleTime: 2 * 60 * 1000,
  });

  const totalCount = listQuery.data?.length ?? 0;
  const abnormalCount = abnormalQuery.data?.length ?? 0;
  const healthScore = computeHealthScore(totalCount, abnormalCount);

  return {
    metrics: listQuery.data ?? [],
    abnormalMetrics: abnormalQuery.data ?? [],
    isLoading: listQuery.isLoading,
    totalCount,
    abnormalCount,
    healthScore,
  };
}

export function useMetricTrend(memberId: string | undefined, testName: string | undefined) {
  return useQuery({
    queryKey: ["metric-trend", memberId, testName],
    queryFn: () => metricsApi.trend(memberId!, testName!),
    enabled: !!memberId && !!testName,
    staleTime: 5 * 60 * 1000,
  });
}
