"use client";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload, FileText, X, CheckCircle } from "lucide-react";
import { toast } from "sonner";
import { cn, formatFileSize } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { reportsApi } from "@/lib/api/reports";
import type { FamilyMember } from "@/types";

const ACCEPTED = {
  "application/pdf": [".pdf"],
  "image/jpeg": [".jpg", ".jpeg"],
  "image/png": [".png"],
};
const MAX_SIZE = 20 * 1024 * 1024; // 20 MB

interface ReportUploadProps {
  member: FamilyMember;
  onSuccess?: () => void;
}

export function ReportUpload({ member, onSuccess }: ReportUploadProps) {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [reportType, setReportType] = useState("blood_test");

  const mutation = useMutation({
    mutationFn: (formData: FormData) => reportsApi.upload(formData),
    onSuccess: () => {
      toast.success("Report uploaded! AI analysis will begin shortly.");
      setFile(null);
      queryClient.invalidateQueries({ queryKey: ["reports", member.id] });
      queryClient.invalidateQueries({ queryKey: ["insights"] });
      onSuccess?.();
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxSize: MAX_SIZE,
    multiple: false,
  });

  const handleSubmit = () => {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    fd.append("family_member_id", member.id);
    fd.append("report_type", reportType);
    mutation.mutate(fd);
  };

  return (
    <div className="space-y-4">
      {/* Report type selector */}
      <div>
        <label className="block text-xs font-medium text-text-secondary mb-1.5">Report Type</label>
        <select
          value={reportType}
          onChange={(e) => setReportType(e.target.value)}
          className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 bg-white text-text-primary focus:outline-none focus:ring-2 focus:ring-brand-blue"
        >
          <option value="blood_test">Blood Test</option>
          <option value="urine_test">Urine Test</option>
          <option value="imaging">Imaging / Scan</option>
          <option value="vaccination">Vaccination</option>
          <option value="other">Other</option>
        </select>
      </div>

      {/* Drop zone */}
      {!file ? (
        <div
          {...getRootProps()}
          className={cn(
            "border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors",
            isDragActive
              ? "border-brand-blue bg-blue-50"
              : "border-surface-border hover:border-brand-blue hover:bg-surface-subtle"
          )}
        >
          <input {...getInputProps()} />
          <Upload className={cn("w-8 h-8 mx-auto mb-3", isDragActive ? "text-brand-blue" : "text-text-muted")} />
          <p className="text-sm font-medium text-text-primary">
            {isDragActive ? "Drop it here" : "Drag & drop or click to upload"}
          </p>
          <p className="text-xs text-text-muted mt-1">PDF, JPG, PNG — max 20 MB</p>
          {fileRejections.length > 0 && (
            <p className="text-xs text-brand-red mt-2">
              {fileRejections[0].errors[0].message}
            </p>
          )}
        </div>
      ) : (
        <div className="flex items-center gap-3 p-4 border border-surface-border rounded-xl bg-surface-subtle">
          <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
            <FileText className="w-5 h-5 text-brand-blue" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-text-primary truncate">{file.name}</p>
            <p className="text-xs text-text-muted">{formatFileSize(file.size)}</p>
          </div>
          <button onClick={() => setFile(null)} className="p-1 rounded-md hover:bg-surface-muted text-text-muted">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <Button
        className="w-full"
        onClick={handleSubmit}
        disabled={!file}
        loading={mutation.isPending}
        icon={<Upload className="w-4 h-4" />}
      >
        {mutation.isPending ? "Uploading…" : "Upload & Analyze"}
      </Button>

      <p className="text-[11px] text-text-muted text-center">
        Your file is encrypted and stored securely. Only you can access it.
      </p>
    </div>
  );
}
