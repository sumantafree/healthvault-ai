"use client";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload, FileText, X } from "lucide-react";
import { toast } from "sonner";
import { cn, formatFileSize } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { prescriptionsApi } from "@/lib/api/prescriptions";
import type { FamilyMember } from "@/types";

const ACCEPTED = {
  "application/pdf": [".pdf"],
  "image/jpeg": [".jpg", ".jpeg"],
  "image/png": [".png"],
};

interface PrescriptionUploadProps {
  member: FamilyMember;
  onSuccess?: () => void;
}

export function PrescriptionUpload({ member, onSuccess }: PrescriptionUploadProps) {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [doctorName, setDoctorName] = useState("");
  const [hospitalName, setHospitalName] = useState("");

  const mutation = useMutation({
    mutationFn: (formData: FormData) => prescriptionsApi.upload(formData),
    onSuccess: () => {
      toast.success("Prescription uploaded! Medicines will be extracted shortly.");
      setFile(null);
      setDoctorName("");
      setHospitalName("");
      queryClient.invalidateQueries({ queryKey: ["prescriptions", member.id] });
      queryClient.invalidateQueries({ queryKey: ["medicines", member.id] });
      queryClient.invalidateQueries({ queryKey: ["medicines-active", member.id] });
      onSuccess?.();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxSize: 20 * 1024 * 1024,
    multiple: false,
  });

  const handleSubmit = () => {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    fd.append("family_member_id", member.id);
    if (doctorName) fd.append("doctor_name", doctorName);
    if (hospitalName) fd.append("hospital_name", hospitalName);
    mutation.mutate(fd);
  };

  return (
    <div className="space-y-4">
      {/* Optional metadata */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1">Doctor Name</label>
          <input
            value={doctorName}
            onChange={(e) => setDoctorName(e.target.value)}
            placeholder="e.g. Dr. Smith"
            className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-blue"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1">Hospital / Clinic</label>
          <input
            value={hospitalName}
            onChange={(e) => setHospitalName(e.target.value)}
            placeholder="e.g. City Hospital"
            className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-blue"
          />
        </div>
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
            {isDragActive ? "Drop prescription here" : "Drag & drop or click to upload"}
          </p>
          <p className="text-xs text-text-muted mt-1">PDF, JPG, PNG — max 20 MB</p>
          {fileRejections.length > 0 && (
            <p className="text-xs text-brand-red mt-2">{fileRejections[0].errors[0].message}</p>
          )}
        </div>
      ) : (
        <div className="flex items-center gap-3 p-4 border border-surface-border rounded-xl bg-surface-subtle">
          <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center flex-shrink-0">
            <FileText className="w-5 h-5 text-brand-green" />
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

      <Button className="w-full" onClick={handleSubmit} disabled={!file} loading={mutation.isPending}
        icon={<Upload className="w-4 h-4" />}>
        {mutation.isPending ? "Uploading…" : "Upload & Extract Medicines"}
      </Button>

      <p className="text-[11px] text-text-muted text-center">
        AI will automatically extract medicine names, dosages, and instructions.
      </p>
    </div>
  );
}
