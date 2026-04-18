import { cn } from "@/lib/utils";
import { Button } from "./Button";

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
  className?: string;
  compact?: boolean;
}

export function EmptyState({ icon, title, description, action, className, compact }: EmptyStateProps) {
  return (
    <div className={cn(
      "flex flex-col items-center justify-center text-center",
      compact ? "py-8" : "py-14",
      className
    )}>
      {icon && (
        <div className="w-14 h-14 rounded-2xl bg-surface-muted flex items-center justify-center mb-4 text-text-muted">
          {icon}
        </div>
      )}
      <h3 className="text-sm font-semibold text-text-primary mb-1">{title}</h3>
      {description && (
        <p className="text-xs text-text-muted max-w-xs leading-relaxed mb-5">{description}</p>
      )}
      {action && (
        <Button size="sm" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}
