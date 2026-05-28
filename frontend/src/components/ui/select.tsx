import * as React from "react";
import * as RS from "@radix-ui/react-select";
import { Check, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

export const Select = RS.Root;
export const SelectValue = RS.Value;

export const SelectTrigger = React.forwardRef<
  React.ElementRef<typeof RS.Trigger>,
  React.ComponentPropsWithoutRef<typeof RS.Trigger>
>(({ className, children, ...props }, ref) => (
  <RS.Trigger
    ref={ref}
    className={cn(
      "flex h-11 w-full items-center justify-between rounded-lg border border-border bg-surface px-3 text-sm",
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-ring",
      className
    )}
    {...props}
  >
    {children}
    <RS.Icon><ChevronDown className="h-4 w-4 opacity-60" /></RS.Icon>
  </RS.Trigger>
));
SelectTrigger.displayName = "SelectTrigger";

export const SelectContent = React.forwardRef<
  React.ElementRef<typeof RS.Content>,
  React.ComponentPropsWithoutRef<typeof RS.Content>
>(({ className, children, ...props }, ref) => (
  <RS.Portal>
    <RS.Content
      ref={ref}
      position="popper"
      sideOffset={6}
      className={cn(
        "z-50 min-w-[10rem] overflow-hidden rounded-lg border border-border bg-surface text-foreground shadow-glass",
        "data-[state=open]:animate-in data-[state=open]:fade-in-0",
        className
      )}
      {...props}
    >
      <RS.Viewport className="p-1">{children}</RS.Viewport>
    </RS.Content>
  </RS.Portal>
));
SelectContent.displayName = "SelectContent";

export const SelectItem = React.forwardRef<
  React.ElementRef<typeof RS.Item>,
  React.ComponentPropsWithoutRef<typeof RS.Item>
>(({ className, children, ...props }, ref) => (
  <RS.Item
    ref={ref}
    className={cn(
      "relative flex cursor-pointer select-none items-center rounded-md px-2 py-2 text-sm pl-7 outline-none",
      "data-[highlighted]:bg-surface2 data-[disabled]:opacity-50",
      className
    )}
    {...props}
  >
    <span className="absolute left-2 flex h-4 w-4 items-center justify-center">
      <RS.ItemIndicator><Check className="h-3.5 w-3.5" /></RS.ItemIndicator>
    </span>
    <RS.ItemText>{children}</RS.ItemText>
  </RS.Item>
));
SelectItem.displayName = "SelectItem";
