"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { apiClient } from "@/lib/api/client";
import { Spinner } from "@/components/ui/Spinner";

export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    const supabase = createClient();

    supabase.auth.onAuthStateChange(async (event, session) => {
      if (event === "SIGNED_IN" && session) {
        // Sync user to our backend
        try {
          await apiClient.post("/auth/me");
        } catch {
          // Non-fatal
        }
        router.replace("/dashboard");
      } else if (event === "SIGNED_OUT") {
        router.replace("/login");
      }
    });
  }, [router]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-3">
      <Spinner size="lg" />
      <p className="text-sm text-text-secondary">Signing you in…</p>
    </div>
  );
}
