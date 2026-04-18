"use client";
import { useEffect } from "react";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  maxWidth?: "sm" | "md" | "lg" | "xl";
  description?: string;
}

export function Modal({ open, onClose, title, description, children, maxWidth = "md" }: ModalProps) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    if (open) {
      document.addEventListener("keydown", handler);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handler);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  const maxWidths = {
    sm: "max-w-sm",
    md: "max-w-md",
    lg: "max-w-lg",
    xl: "max-w-2xl",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-fade-in"
        onClick={onClose}
      />

      {/* Sheet on mobile, centered modal on desktop */}
      <div className={cn(
        "relative w-full bg-white shadow-modal animate-slide-up",
        "rounded-t-2xl sm:rounded-2xl",
        "max-h-[92vh] sm:max-h-[85vh] flex flex-col",
        maxWidths[maxWidth]
      )}>
        {/* Drag handle (mobile) */}
        <div className="sm:hidden flex justify-center pt-3 pb-1 flex-shrink-0">
          <div className="w-10 h-1 bg-surface-border rounded-full" />
        </div>

        {/* Header */}
        <div className="flex items-start justify-between px-5 py-4 border-b border-surface-border flex-shrink-0">
          <div>
            <h2 className="text-base font-semibold text-text-primary leading-tight">{title}</h2>
            {description && <p className="text-xs text-text-muted mt-0.5">{description}</p>}
          </div>
          <button
            onClick={onClose}
            className="p-1.5 -mr-1 -mt-1 rounded-xl hover:bg-surface-muted text-text-muted hover:text-text-primary transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Body — scrollable */}
        <div className="p-5 overflow-y-auto flex-1">{children}</div>
      </div>
    </div>
  );
}
