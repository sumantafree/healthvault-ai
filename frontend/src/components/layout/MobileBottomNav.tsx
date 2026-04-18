"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, FileText, TrendingUp, Lightbulb, Pill } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard",     icon: LayoutDashboard, label: "Home"     },
  { href: "/reports",       icon: FileText,        label: "Reports"  },
  { href: "/metrics",       icon: TrendingUp,      label: "Trends"   },
  { href: "/insights",      icon: Lightbulb,       label: "Insights" },
  { href: "/prescriptions", icon: Pill,            label: "Meds"     },
];

export function MobileBottomNav() {
  const pathname = usePathname();

  return (
    <nav className="lg:hidden fixed bottom-0 inset-x-0 z-40 bg-white border-t border-surface-border">
      <div className="flex">
        {NAV.map(({ href, icon: Icon, label }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex-1 flex flex-col items-center justify-center py-2.5 gap-0.5 text-[10px] font-medium transition-colors",
                active ? "text-brand-blue" : "text-text-muted hover:text-text-secondary"
              )}
            >
              <Icon className={cn("w-5 h-5", active && "text-brand-blue")} />
              {label}
              {active && (
                <span className="absolute bottom-0 w-5 h-0.5 bg-brand-blue rounded-t-full" />
              )}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
