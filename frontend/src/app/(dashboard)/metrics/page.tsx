"use client";
import { useState } from "react";
import { Header } from "@/components/layout/Header";
import { MetricTrendChart } from "@/components/charts/MetricTrendChart";
import { MetricStatusBadge } from "@/components/ui/Badge";
import { PageLoader } from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { Card } from "@/components/ui/Card";
import { useSelectedMember } from "@/hooks/useFamilyMembers";
import { useMetrics, useMetricTrend } from "@/hooks/useMetrics";
import { formatDate } from "@/lib/utils";
import { TrendingUp } from "lucide-react";

export default function MetricsPage() {
  const member = useSelectedMember();
  const { metrics, isLoading } = useMetrics(member?.id);
  const [selectedTest, setSelectedTest] = useState<string | null>(null);
  const { data: trend, isLoading: trendLoading } = useMetricTrend(member?.id, selectedTest ?? undefined);

  // Group metrics by category
  const categories = Array.from(new Set(metrics.map((m) => m.category ?? "Other"))).sort();
  const metricsByCategory = categories.reduce<Record<string, typeof metrics>>((acc, cat) => {
    acc[cat] = metrics.filter((m) => (m.category ?? "Other") === cat);
    return acc;
  }, {});

  // Get unique test names for trend selection
  const uniqueTests = Array.from(new Set(metrics.map((m) => m.test_name))).sort();

  if (isLoading) return <><Header title="Trends" /><PageLoader /></>;

  return (
    <>
      <Header title="Health Trends" subtitle={member?.name} />
      <div className="p-6 space-y-6">

        {metrics.length === 0 ? (
          <EmptyState
            icon={<TrendingUp className="w-10 h-10" />}
            title="No metrics yet"
            description="Upload a health report to see trends over time."
          />
        ) : (
          <>
            {/* Test name selector for trend chart */}
            <Card>
              <p className="text-xs font-semibold text-text-secondary uppercase tracking-wide mb-3">
                Select a test to view trend
              </p>
              <div className="flex flex-wrap gap-2">
                {uniqueTests.map((t) => (
                  <button
                    key={t}
                    onClick={() => setSelectedTest(t === selectedTest ? null : t)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                      selectedTest === t
                        ? "bg-brand-blue text-white"
                        : "bg-surface-muted text-text-secondary hover:bg-slate-200"
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </Card>

            {/* Trend chart */}
            {selectedTest && (
              <div className="animate-fade-in">
                {trendLoading ? (
                  <div className="h-64 bg-surface-muted rounded-xl animate-pulse" />
                ) : trend ? (
                  <MetricTrendChart trend={trend} height={240} />
                ) : null}
              </div>
            )}

            {/* Metrics by category */}
            {categories.map((cat) => (
              <div key={cat}>
                <h2 className="text-sm font-semibold text-text-secondary mb-3">{cat}</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
                  {metricsByCategory[cat].map((m) => (
                    <button
                      key={m.id}
                      onClick={() => setSelectedTest(m.test_name)}
                      className="text-left bg-white border border-surface-border rounded-xl p-4 hover:shadow-card-hover transition-shadow"
                    >
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <p className="text-sm font-semibold text-text-primary leading-snug">{m.test_name}</p>
                        <MetricStatusBadge status={m.status} />
                      </div>
                      <p className="text-xl font-bold text-text-primary tabular-nums">
                        {m.value}
                        <span className="text-sm font-normal text-text-muted ml-1">{m.unit}</span>
                      </p>
                      {m.normal_range_text && (
                        <p className="text-[11px] text-text-muted mt-1">Normal: {m.normal_range_text}</p>
                      )}
                      <p className="text-[11px] text-text-muted">{formatDate(m.measured_at)}</p>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </>
        )}
      </div>
    </>
  );
}
