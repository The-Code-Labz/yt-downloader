import * as React from "react";
import { cn } from "@/lib/utils";

export function Badge({
  className,
  variant = "default",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & {
  variant?: "default" | "audio" | "video" | "status";
}) {
  const styles: Record<string, string> = {
    default: "bg-surface2 text-foreground border border-border",
    audio:   "bg-blue-500/15 text-blue-300 border border-blue-500/30",
    video:   "bg-accent/15 text-accent border border-accent/30",
    status:  "bg-surface2 text-muted border border-border",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium uppercase tracking-wide",
        styles[variant],
        className
      )}
      {...props}
    />
  );
}
