import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { Sidebar } from "@/components/layout/Sidebar";
import { MobileBottomNav } from "@/components/layout/MobileBottomNav";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const supabase = createClient();
  const { data } = await supabase.auth.getUser();
  if (!data.user) redirect("/login");

  return (
    <div className="flex h-screen overflow-hidden bg-surface-subtle">
      <Sidebar />
      {/* Main content — offset on desktop, full-width on mobile */}
      <main className="flex-1 lg:ml-[260px] overflow-y-auto pb-16 lg:pb-0">
        {children}
      </main>
      {/* Mobile bottom navigation */}
      <MobileBottomNav />
    </div>
  );
}
