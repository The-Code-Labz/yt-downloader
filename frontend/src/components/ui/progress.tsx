import * as React from "react";
import * as RP from "@radix-ui/react-progress";
import { cn } from "@/lib/utils";

export function Progress({
  value = 0,
  className,
}: { value?: number; className?: string }) {
  return (
    <RP.Root
      value={value}
      className={cn("relative h-1.5 w-full overflow-hidden rounded-full bg-surface2", className)}
    >
      <RP.Indicator
        className="h-full w-full flex-1 bg-gradient-to-r from-accent to-orange-400 transition-transform duration-500"
        style={{ transform: `translateX(-${100 - Math.min(100, Math.max(0, value))}%)` }}
      />
    </RP.Root>
  );
}
