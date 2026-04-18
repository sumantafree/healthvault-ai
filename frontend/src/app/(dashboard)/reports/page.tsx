"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { FileText, Upload, Trash2, RefreshCw, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { Header } from "@/components/layout/Header";
import { ReportUpload } from "@/components/reports/ReportUpload";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { RiskBadge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { Card } from "@/components/ui/Card";
import { PageLoader } from "@/components/ui/Spinner";
import { useSelectedMember } from "@/hooks/useFamilyMembers";
import { reportsApi } from "@/lib/api/reports";
import { insightsApi } from "@/lib/api/insights";
import { formatDate, formatRelative, formatFileSize } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { HealthReport, ProcessingStatus } from "@/types";
import { PROCESSING_STATUS_CONFIG } from "@/types";

export default function ReportsPage() {
  const member = useSelectedMember();
  const queryClient = useQueryClient();
  const [uploadOpen, setUploadOpen] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["reports", member?.id],
    queryFn: () => reportsApi.list(member!.id),
    enabled: !!member?.id,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => reportsApi.delete(id),
    onSuccess: () => {
      toast.success("Report deleted.");
      queryClient.invalidateQueries({ queryKey: ["reports", member?.id] });
    },
    onError: () => toast.error("Failed to delete report."),
  });

  const reanalyzeMutation = useMutation({
    mutationFn: (id: string) => insightsApi.reanalyze(id),
    onSuccess: () => {
      toast.success("Re-analysis started.");
      queryClient.invalidateQueries({ queryKey: ["reports", member?.id] });
    },
    onError: () => toast.error("Failed to start re-analysis."),
  });

  if (!member) return <><Header title="Reports" /><EmptyState title="Select a family member" className="mt-20" /></>;
  if (isLoading) return <><Header title="Reports" /><PageLoader /></>;

  const reports = data?.items ?? [];

  return (
    <>
      <Header title="Health Reports" subtitle={member.name} />
      <div className="p-6 space-y-5">
        <div className="flex justify-end">
          <Button icon={<Upload className="w-3.5 h-3.5" />} onClick={() => setUploadOpen(true)}>
            Upload Report
          </Button>
        </div>

        {reports.length === 0 ? (
          <EmptyState
            icon={<FileText className="w-10 h-10" />}
            title="No reports yet"
            description="Upload lab reports, blood tests, and medical documents."
            action={{ label: "Upload First Report", onClick: () => setUploadOpen(true) }}
          />
        ) : (
          <div className="space-y-3">
            {reports.map((r) => (
              <ReportRow
                key={r.id}
                report={r}
                onDelete={() => deleteMutation.mutate(r.id)}
                onReanalyze={() => reanalyzeMutation.mutate(r.id)}
                isDeleting={deleteMutation.isPending}
              />
            ))}
          </div>
        )}
      </div>

      <Modal open={uploadOpen} onClose={() => setUploadOpen(false)} title={`Upload Report for ${member.name}`}>
        <ReportUpload member={member} onSuccess={() => setUploadOpen(false)} />
      </Modal>
    </>
  );
}

function ReportRow({
  report,
  onDelete,
  onReanalyze,
  isDeleting,
}: {
  report: HealthReport;
  onDelete: () => void;
  onReanalyze: () => void;
  isDeleting: boolean;
}) {
  const statusCfg = PROCESSING_STATUS_CONFIG[report.processing_status];

  return (
    <Card className="flex items-center gap-4">
      <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
        <FileText className="w-5 h-5 text-brand-blue" />
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <p className="text-sm font-semibold text-text-primary truncate">{report.file_name}</p>
          {report.processing_status === "done" && <RiskBadge level={report.risk_level} />}
        </div>
        <div className="flex items-center gap-3 mt-0.5 flex-wrap">
          <span className={cn("text-xs font-medium", statusCfg.color)}>{statusCfg.label}</span>
          {report.lab_name && <span className="text-xs text-text-muted">{report.lab_name}</span>}
          {report.report_date && <span className="text-xs text-text-muted">{formatDate(report.report_date)}</span>}
          <span className="text-xs text-text-muted">{formatRelative(report.created_at)}</span>
          {report.file_size_bytes && (
            <span className="text-xs text-text-muted">{formatFileSize(report.file_size_bytes)}</span>
          )}
        </div>
        {report.ai_summary && (
          <p className="text-xs text-text-secondary mt-1 line-clamp-2">{report.ai_summary}</p>
        )}
      </div>

      <div className="flex items-center gap-1.5 flex-shrink-0">
        {report.processing_status === "failed" && (
          <Button variant="ghost" size="sm" icon={<RefreshCw className="w-3.5 h-3.5" />} onClick={onReanalyze}>
            Retry
          </Button>
        )}
        <button
          onClick={onDelete}
          disabled={isDeleting}
          className="p-2 rounded-lg hover:bg-red-50 hover:text-brand-red text-text-muted transition-colors"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </Card>
  );
}
