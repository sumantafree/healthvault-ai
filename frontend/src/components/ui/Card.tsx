import { cn } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
  gradient?: boolean;
  accent?: "blue" | "green" | "yellow" | "red" | "purple" | "teal";
}

const ACCENT_STYLES = {
  blue:   "before:from-blue-500 before:to-indigo-500",
  green:  "before:from-emerald-500 before:to-teal-500",
  yellow: "before:from-amber-400 before:to-orange-500",
  red:    "before:from-red-500 before:to-rose-500",
  purple: "before:from-violet-500 before:to-purple-500",
  teal:   "before:from-teal-500 before:to-cyan-500",
};

export function Card({ children, className, hover, onClick, gradient, accent }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "bg-white rounded-card border border-surface-border shadow-card p-5",
        hover && "transition-all duration-200 cursor-pointer hover:shadow-card-hover hover:-translate-y-0.5",
        gradient && "bg-gradient-card",
        onClick && "cursor-pointer",
        className
      )}
    >
      {accent && (
        <div className={cn(
          "h-0.5 w-full -mt-5 mb-4 mx-auto rounded-t-card bg-gradient-to-r",
          `from-${accent === "blue" ? "blue" : accent === "green" ? "emerald" : accent === "yellow" ? "amber" : accent === "red" ? "red" : accent === "purple" ? "violet" : "teal"}-500`,
          `to-${accent === "blue" ? "indigo" : accent === "green" ? "teal" : accent === "yellow" ? "orange" : accent === "red" ? "rose" : accent === "purple" ? "purple" : "cyan"}-500`,
        )} />
      )}
      {children}
    </div>
  );
}

export function CardHeader({ children, className, action }: {
  children: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className={cn("flex items-center justify-between mb-4", className)}>
      <div>{children}</div>
      {action && <div>{action}</div>}
    </div>
  );
}

export function CardTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <h3 className={cn("text-xs font-semibold text-text-muted uppercase tracking-widest", className)}>
      {children}
    </h3>
  );
}
