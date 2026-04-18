"use client";
import { ChevronDown, UserCircle, Check } from "lucide-react";
import { useState } from "react";
import { cn, getInitials } from "@/lib/utils";
import { useFamilyMembers } from "@/hooks/useFamilyMembers";
import { useMemberStore } from "@/store/member";
import type { FamilyMember } from "@/types";

export function MemberSelector() {
  const { members, isLoading } = useFamilyMembers();
  const { selectedMember, setSelectedMember } = useMemberStore();
  const [open, setOpen] = useState(false);

  if (isLoading) {
    return <div className="h-9 w-36 skeleton rounded-xl" />;
  }

  if (members.length === 0) {
    return (
      <div className="flex items-center gap-2 text-sm text-text-muted px-3 py-2 rounded-xl border border-dashed border-surface-border">
        <UserCircle className="w-4 h-4" />
        <span className="text-xs">No members</span>
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 pl-2 pr-3 py-1.5 rounded-xl border border-surface-border bg-surface-subtle hover:bg-surface-muted transition-colors text-sm"
      >
        <MemberAvatar member={selectedMember} size="sm" />
        <span className="font-medium text-text-primary max-w-[100px] truncate text-xs sm:text-sm">
          {selectedMember?.name ?? "Select member"}
        </span>
        <ChevronDown className={cn("w-3.5 h-3.5 text-text-muted transition-transform duration-200", open && "rotate-180")} />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full mt-2 w-56 bg-white border border-surface-border rounded-2xl shadow-card-hover z-20 py-2 animate-scale-in overflow-hidden">
            <div className="px-3 pb-2 border-b border-surface-border mb-1">
              <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">Family Members</p>
            </div>
            {members.map((m) => {
              const isSelected = selectedMember?.id === m.id;
              return (
                <button
                  key={m.id}
                  onClick={() => { setSelectedMember(m); setOpen(false); }}
                  className={cn(
                    "w-full flex items-center gap-2.5 px-3 py-2.5 text-sm transition-colors text-left",
                    isSelected ? "bg-blue-50" : "hover:bg-surface-subtle"
                  )}
                >
                  <MemberAvatar member={m} size="sm" />
                  <div className="min-w-0 flex-1">
                    <p className={cn("font-medium truncate text-sm", isSelected ? "text-brand-blue" : "text-text-primary")}>
                      {m.name}
                    </p>
                    {m.is_primary && (
                      <p className="text-[10px] text-text-muted">Primary member</p>
                    )}
                  </div>
                  {isSelected && <Check className="w-3.5 h-3.5 text-brand-blue flex-shrink-0" />}
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

// Avatar color palette — health-themed
const AVATAR_COLORS = [
  "bg-blue-100 text-blue-700",
  "bg-violet-100 text-violet-700",
  "bg-emerald-100 text-emerald-700",
  "bg-amber-100 text-amber-700",
  "bg-pink-100 text-pink-700",
  "bg-teal-100 text-teal-700",
];

export function MemberAvatar({
  member,
  size = "md",
}: {
  member: FamilyMember | null;
  size?: "sm" | "md" | "lg";
}) {
  const sizes = {
    sm: "w-6 h-6 text-[10px]",
    md: "w-8 h-8 text-xs",
    lg: "w-12 h-12 text-sm font-semibold",
  };
  const initials = getInitials(member?.name);
  const colorIdx = member ? member.name.charCodeAt(0) % AVATAR_COLORS.length : 0;

  return (
    <span className={cn(
      "inline-flex items-center justify-center rounded-full font-semibold flex-shrink-0 select-none",
      sizes[size],
      AVATAR_COLORS[colorIdx]
    )}>
      {initials}
    </span>
  );
}
