"use client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Users, Plus, Trash2, Edit2 } from "lucide-react";
import { toast } from "sonner";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { EmptyState } from "@/components/ui/EmptyState";
import { MemberAvatar } from "@/components/layout/MemberSelector";
import { useFamilyMembers } from "@/hooks/useFamilyMembers";
import { useMemberStore } from "@/store/member";
import { formatDate } from "@/lib/utils";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  date_of_birth: z.string().optional(),
  gender: z.enum(["male", "female", "other"]).default("other"),
  blood_type: z.enum(["A+","A-","B+","B-","AB+","AB-","O+","O-","unknown"]).default("unknown"),
  height_cm: z.preprocess((v) => (v === "" ? undefined : Number(v)), z.number().positive().optional()),
  weight_kg: z.preprocess((v) => (v === "" ? undefined : Number(v)), z.number().positive().optional()),
  is_primary: z.boolean().default(false),
});

type FormData = z.infer<typeof schema>;

export default function FamilyPage() {
  const { members, isLoading, createMember, deleteMember, isCreating } = useFamilyMembers();
  const { selectedMember, setSelectedMember } = useMemberStore();
  const [addOpen, setAddOpen] = useState(false);

  const form = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    try {
      await createMember(data);
      toast.success(`${data.name} added to your family.`);
      form.reset();
      setAddOpen(false);
    } catch (e: any) {
      toast.error(e.message);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Remove ${name} from your family? This will delete all their health data.`)) return;
    try {
      await deleteMember(id);
      toast.success(`${name} removed.`);
    } catch {
      toast.error("Failed to delete member.");
    }
  };

  return (
    <>
      <Header title="Family Members" />
      <div className="p-6 space-y-5">
        <div className="flex justify-end">
          <Button icon={<Plus className="w-3.5 h-3.5" />} onClick={() => setAddOpen(true)}>
            Add Member
          </Button>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2].map((i) => (
              <div key={i} className="h-32 bg-surface-muted rounded-xl animate-pulse" />
            ))}
          </div>
        ) : members.length === 0 ? (
          <EmptyState
            icon={<Users className="w-10 h-10" />}
            title="No family members yet"
            description="Add yourself and your family to start tracking health together."
            action={{ label: "Add First Member", onClick: () => setAddOpen(true) }}
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {members.map((m) => (
              <Card
                key={m.id}
                hover
                onClick={() => setSelectedMember(m)}
                className={`relative ${selectedMember?.id === m.id ? "ring-2 ring-brand-blue" : ""}`}
              >
                {m.is_primary && (
                  <span className="absolute top-3 right-3 text-[10px] font-semibold bg-blue-50 text-brand-blue px-2 py-0.5 rounded-full">
                    Primary
                  </span>
                )}
                <div className="flex items-start gap-3">
                  <MemberAvatar member={m} size="lg" />
                  <div className="min-w-0">
                    <p className="font-semibold text-text-primary truncate">{m.name}</p>
                    <p className="text-xs text-text-muted">
                      {m.age ? `${m.age} yrs · ` : ""}{m.gender} · {m.blood_type}
                    </p>
                    {m.date_of_birth && (
                      <p className="text-xs text-text-muted">{formatDate(m.date_of_birth)}</p>
                    )}
                  </div>
                </div>

                <div className="mt-3 flex gap-3 text-xs text-text-muted">
                  {m.height_cm && <span>{m.height_cm} cm</span>}
                  {m.weight_kg && <span>{m.weight_kg} kg</span>}
                  {m.bmi && <span>BMI {m.bmi}</span>}
                </div>

                <div className="mt-3 flex justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => handleDelete(m.id, m.name)}
                    className="p-1.5 rounded-lg hover:bg-red-50 hover:text-brand-red text-text-muted transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Add Member Modal */}
      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="Add Family Member" maxWidth="md">
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <label className="block text-xs font-medium text-text-secondary mb-1">Full Name *</label>
              <input
                {...form.register("name")}
                className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-blue"
                placeholder="e.g. John Doe"
              />
              {form.formState.errors.name && (
                <p className="text-xs text-brand-red mt-0.5">{form.formState.errors.name.message}</p>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Date of Birth</label>
              <input
                type="date"
                {...form.register("date_of_birth")}
                className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-blue"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Gender</label>
              <select
                {...form.register("gender")}
                className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-blue"
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Blood Type</label>
              <select
                {...form.register("blood_type")}
                className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-blue"
              >
                {["A+","A-","B+","B-","AB+","AB-","O+","O-","unknown"].map((bt) => (
                  <option key={bt} value={bt}>{bt}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Height (cm)</label>
              <input
                type="number"
                {...form.register("height_cm")}
                placeholder="e.g. 170"
                className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-blue"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Weight (kg)</label>
              <input
                type="number"
                step="0.1"
                {...form.register("weight_kg")}
                placeholder="e.g. 70"
                className="w-full text-sm border border-surface-border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-blue"
              />
            </div>

            <div className="col-span-2 flex items-center gap-2">
              <input
                type="checkbox"
                id="is_primary"
                {...form.register("is_primary")}
                className="rounded border-surface-border text-brand-blue focus:ring-brand-blue"
              />
              <label htmlFor="is_primary" className="text-sm text-text-primary cursor-pointer">
                This is my own profile (primary member)
              </label>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => setAddOpen(false)}>Cancel</Button>
            <Button type="submit" loading={isCreating}>Add Member</Button>
          </div>
        </form>
      </Modal>
    </>
  );
}
