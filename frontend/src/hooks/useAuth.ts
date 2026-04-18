"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { User as SupabaseUser, Session } from "@supabase/supabase-js";
import { createClient } from "@/lib/supabase/client";
import { apiClient } from "@/lib/api/client";

export function useAuth() {
  const [user, setUser] = useState<SupabaseUser | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const supabase = createClient();

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setUser(data.session?.user ?? null);
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, session) => {
        setUser(session?.user ?? null);
        // Sync user to our DB on login
        if (session?.user) {
          try {
            await apiClient.post("/auth/me");
          } catch {
            // Non-fatal — user may already exist
          }
        }
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  const signInWithGoogle = async () => {
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
        queryParams: { access_type: "offline", prompt: "consent" },
      },
    });
  };

  const signOut = async () => {
    await supabase.auth.signOut();
    router.push("/login");
  };

  return { user, loading, signInWithGoogle, signOut };
}
