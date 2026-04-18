"use client";
import { Activity } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { MetricStatusBadge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import type { HealthMetric } from "@/types";
import { formatDate, cn } from "@/lib/utils";

interface MetricsSummaryProps {
  metrics: HealthMetric[];
  showAbnormalOnly?: boolean;
}

export function MetricsSummary({ metrics, showAbnormalOnly = false }: MetricsSummaryProps) {
  const displayed = showAbnormalOnly
    ? metrics.filter((m) => m.is_abnormal)
    : metrics.slice(0, 8);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{showAbnormalOnly ? "Needs Attention" : "Recent Metrics"}</CardTitle>
      </CardHeader>

      {displayed.length === 0 ? (
        <EmptyState
          compact
          icon={<Activity className="w-6 h-6" />}
          title={showAbnormalOnly ? "All values normal" : "No metrics yet"}
          description={showAbnormalOnly
            ? "Great news — everything looks good."
            : "Upload a lab report to see your metrics."}
        />
      ) : (
        <div className="divide-y divide-surface-border">
          {displayed.map((m) => (
            <MetricRow key={m.id} metric={m} />
          ))}
        </div>
      )}
    </Card>
  );
}

function MetricRow({ metric: m }: { metric: HealthMetric }) {
  const isAbnormal = m.is_abnormal;
  return (
    <div className="flex items-center justify-between py-3 first:pt-0 last:pb-0 group">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className={cn(
            "w-1.5 h-1.5 rounded-full flex-shrink-0",
            isAbnormal ? "bg-red-500" : "bg-emerald-500"
          )} />
          <p className="text-sm font-medium text-text-primary truncate">{m.test_name}</p>
        </div>
        <p className="text-[11px] text-text-muted ml-3.5">{formatDate(m.measured_at)}</p>
      </div>
      <div className="flex items-center gap-2.5 ml-3 flex-shrink-0">
        <span className={cn(
          "text-sm font-semibold tabular-nums",
          isAbnormal ? "text-red-600" : "text-text-primary"
        )}>
          {m.value} <span className="text-xs font-normal text-text-muted">{m.unit ?? ""}</span>
        </span>
        <MetricStatusBadge status={m.status} />
      </div>
    </div>
  );
}
