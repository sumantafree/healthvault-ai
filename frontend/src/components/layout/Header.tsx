"use client";
import { Bell, Menu } from "lucide-react";
import { MemberSelector } from "./MemberSelector";
import { useAuth } from "@/hooks/useAuth";
import { useSidebarStore } from "@/store/sidebar";
import { getInitials } from "@/lib/utils";
import Image from "next/image";

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export function Header({ title, subtitle }: HeaderProps) {
  const { user } = useAuth();
  const toggle = useSidebarStore((s) => s.toggle);

  return (
    <header className="h-16 flex items-center justify-between px-4 sm:px-6 bg-white border-b border-surface-border sticky top-0 z-30">
      <div className="flex items-center gap-3 min-w-0">
        {/* Hamburger — mobile only */}
        <button
          onClick={toggle}
          className="lg:hidden p-2 rounded-xl hover:bg-surface-muted text-text-muted hover:text-text-primary transition-colors -ml-1"
          aria-label="Toggle menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="min-w-0">
          <h1 className="text-base sm:text-lg font-bold text-text-primary leading-tight truncate">{title}</h1>
          {subtitle && (
            <p className="text-xs text-text-muted mt-0.5 hidden sm:block">{subtitle}</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
        <div className="hidden sm:block">
          <MemberSelector />
        </div>

        {/* Notification bell */}
        <button className="relative w-9 h-9 flex items-center justify-center rounded-xl hover:bg-surface-muted text-text-muted hover:text-text-primary transition-colors">
          <Bell className="w-4 h-4" />
          <span className="absolute top-2 right-2 w-1.5 h-1.5 bg-brand-red rounded-full" />
        </button>

        {/* User avatar */}
        <div className="w-8 h-8 rounded-full overflow-hidden ring-2 ring-surface-border">
          {user?.user_metadata?.avatar_url ? (
            <Image
              src={user.user_metadata.avatar_url}
              alt="avatar"
              width={32}
              height={32}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full bg-gradient-brand flex items-center justify-center">
              <span className="text-[11px] font-bold text-white">
                {getInitials(user?.user_metadata?.full_name ?? user?.email)}
              </span>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
