"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { familyApi } from "@/lib/api/family";
import { useMemberStore } from "@/store/member";
import type { FamilyMember, FamilyMemberCreate } from "@/types";

export function useFamilyMembers() {
  const queryClient = useQueryClient();
  const { selectedMember, setSelectedMember } = useMemberStore();

  const query = useQuery({
    queryKey: ["family-members"],
    queryFn: familyApi.list,
    staleTime: 5 * 60 * 1000,
  });

  // Auto-select primary member or first member on load
  useEffect(() => {
    if (query.data && query.data.length > 0 && !selectedMember) {
      const primary = query.data.find((m) => m.is_primary) ?? query.data[0];
      setSelectedMember(primary);
    }
  }, [query.data, selectedMember, setSelectedMember]);

  const createMutation = useMutation({
    mutationFn: (payload: FamilyMemberCreate) => familyApi.create(payload),
    onSuccess: (newMember) => {
      queryClient.invalidateQueries({ queryKey: ["family-members"] });
      setSelectedMember(newMember);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<FamilyMemberCreate> }) =>
      familyApi.update(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["family-members"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => familyApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["family-members"] }),
  });

  return {
    members: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
    createMember: createMutation.mutateAsync,
    updateMember: updateMutation.mutateAsync,
    deleteMember: deleteMutation.mutateAsync,
    isCreating: createMutation.isPending,
  };
}

export function useSelectedMember() {
  return useMemberStore((s) => s.selectedMember);
}
