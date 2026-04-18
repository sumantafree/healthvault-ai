import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "outline";
  size?: "xs" | "sm" | "md" | "lg";
  loading?: boolean;
  icon?: React.ReactNode;
  fullWidth?: boolean;
}

export function Button({
  children,
  variant = "primary",
  size = "md",
  loading,
  icon,
  className,
  disabled,
  fullWidth,
  ...props
}: ButtonProps) {
  const variants = {
    primary:   "bg-gradient-brand text-white shadow-sm hover:opacity-90 active:scale-95",
    secondary: "bg-surface-muted text-text-primary border border-surface-border hover:bg-slate-100 active:scale-95",
    ghost:     "text-text-secondary hover:bg-surface-muted hover:text-text-primary active:scale-95",
    danger:    "bg-red-50 text-red-600 border border-red-200 hover:bg-red-100 active:scale-95",
    outline:   "bg-transparent text-brand-blue border border-brand-blue hover:bg-blue-50 active:scale-95",
  };
  const sizes = {
    xs: "h-7 px-2.5 text-xs gap-1",
    sm: "h-8 px-3 text-xs gap-1.5",
    md: "h-9 px-4 text-sm gap-2",
    lg: "h-11 px-6 text-sm gap-2.5 font-semibold",
  };

  return (
    <button
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center justify-center font-medium rounded-xl transition-all duration-150",
        "disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue focus-visible:ring-offset-2",
        variants[variant],
        sizes[size],
        fullWidth && "w-full",
        className
      )}
      {...props}
    >
      {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin flex-shrink-0" /> : (icon && <span className="flex-shrink-0">{icon}</span>)}
      {children}
    </button>
  );
}
