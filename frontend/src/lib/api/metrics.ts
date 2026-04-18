import { apiClient } from "./client";
import type { HealthMetric, MetricTrend } from "@/types";

export const metricsApi = {
  list: (familyMemberId: string, params?: { category?: string; status?: string }) =>
    apiClient
      .get<HealthMetric[]>("/metrics/", { params: { family_member_id: familyMemberId, ...params } })
      .then((r) => r.data),

  abnormal: (familyMemberId: string) =>
    apiClient
      .get<HealthMetric[]>("/metrics/abnormal", { params: { family_member_id: familyMemberId } })
      .then((r) => r.data),

  trend: (familyMemberId: string, testName: string) =>
    apiClient
      .get<MetricTrend>("/metrics/trends", {
        params: { family_member_id: familyMemberId, test_name: testName },
      })
      .then((r) => r.data),
};
