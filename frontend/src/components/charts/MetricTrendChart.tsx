"use client";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, ResponsiveContainer, ReferenceArea,
} from "recharts";
import { format, parseISO } from "date-fns";
import type { MetricTrend } from "@/types";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { TrendingUp } from "lucide-react";

interface MetricTrendChartProps {
  trend: MetricTrend;
  height?: number;
}

const STATUS_COLORS: Record<string, string> = {
  normal:       "#34C759",
  borderline:   "#FF9500",
  abnormal_low: "#FF3B30",
  abnormal_high:"#FF3B30",
};

export function MetricTrendChart({ trend, height = 220 }: MetricTrendChartProps) {
  if (trend.data_points.length === 0) {
    return (
      <Card>
        <EmptyState icon={<TrendingUp className="w-8 h-8" />} title="No trend data" />
      </Card>
    );
  }

  const chartData = trend.data_points.map((dp) => ({
    date: format(parseISO(dp.measured_at), "MMM d"),
    value: dp.value,
    status: dp.status,
    fill: STATUS_COLORS[dp.status] ?? "#4A90E2",
  }));

  const hasRange = trend.normal_range_min !== null && trend.normal_range_max !== null;
  const allValues = chartData.map((d) => d.value);
  const yMin = Math.min(...allValues, trend.normal_range_min ?? Infinity) * 0.9;
  const yMax = Math.max(...allValues, trend.normal_range_max ?? -Infinity) * 1.1;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between mb-2">
        <CardTitle>{trend.test_name}</CardTitle>
        {trend.unit && <span className="text-xs text-text-muted">({trend.unit})</span>}
      </CardHeader>

      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: "#94A3B8" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={[yMin, yMax]}
            tick={{ fontSize: 11, fill: "#94A3B8" }}
            axisLine={false}
            tickLine={false}
            width={40}
          />
          <Tooltip
            contentStyle={{ borderRadius: 8, border: "1px solid #E2E8F0", fontSize: 12 }}
            formatter={(v: number) => [`${v} ${trend.unit ?? ""}`, trend.test_name]}
          />

          {/* Normal range shading */}
          {hasRange && (
            <ReferenceArea
              y1={trend.normal_range_min!}
              y2={trend.normal_range_max!}
              fill="#34C759"
              fillOpacity={0.06}
              strokeOpacity={0}
            />
          )}
          {hasRange && (
            <>
              <ReferenceLine y={trend.normal_range_min!} stroke="#34C759" strokeDasharray="4 4" strokeOpacity={0.5} />
              <ReferenceLine y={trend.normal_range_max!} stroke="#34C759" strokeDasharray="4 4" strokeOpacity={0.5} />
            </>
          )}

          <Line
            type="monotone"
            dataKey="value"
            stroke="#4A90E2"
            strokeWidth={2.5}
            dot={(props) => {
              const { cx, cy, payload } = props;
              return (
                <circle key={`dot-${cx}-${cy}`} cx={cx} cy={cy} r={4}
                  fill={payload.fill} stroke="white" strokeWidth={2} />
              );
            }}
            activeDot={{ r: 6, stroke: "white", strokeWidth: 2 }}
          />
        </LineChart>
      </ResponsiveContainer>

      {hasRange && (
        <p className="text-[11px] text-text-muted mt-2">
          Normal range: {trend.normal_range_min} – {trend.normal_range_max} {trend.unit}
        </p>
      )}
    </Card>
  );
}
