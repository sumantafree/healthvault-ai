// Zustand store — currently selected family member (persisted to sessionStorage)
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { FamilyMember } from "@/types";

interface MemberStore {
  selectedMember: FamilyMember | null;
  setSelectedMember: (member: FamilyMember) => void;
  clearSelectedMember: () => void;
}

export const useMemberStore = create<MemberStore>()(
  persist(
    (set) => ({
      selectedMember: null,
      setSelectedMember: (member) => set({ selectedMember: member }),
      clearSelectedMember: () => set({ selectedMember: null }),
    }),
    {
      name: "healthvault-selected-member",
      storage: createJSONStorage(() => sessionStorage),
    }
  )
);
