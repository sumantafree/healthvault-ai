import { cn } from "@/lib/utils";

export function Spinner({ size = "md", className }: { size?: "sm" | "md" | "lg"; className?: string }) {
  const sizes = { sm: "w-4 h-4", md: "w-6 h-6", lg: "w-10 h-10" };
  return (
    <div
      className={cn(
        "rounded-full border-surface-border border-t-brand-blue animate-spin",
        sizes[size],
        className
      )}
      style={{ borderWidth: size === "lg" ? 3 : 2 }}
    />
  );
}

export function PageLoader() {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="flex flex-col items-center gap-3">
        <Spinner size="lg" />
        <p className="text-xs text-text-muted animate-pulse">Loading…</p>
      </div>
    </div>
  );
}
