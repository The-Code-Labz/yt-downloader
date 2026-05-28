import * as React from "react";
import * as RT from "@radix-ui/react-toast";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

type Toast = { id: number; title: string; description?: string; variant?: "default" | "error" | "success" };
const ToastCtx = React.createContext<(t: Omit<Toast, "id">) => void>(() => {});

export function useToast() { return React.useContext(ToastCtx); }

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<Toast[]>([]);
  const push = React.useCallback((t: Omit<Toast, "id">) => {
    const id = Date.now() + Math.random();
    setToasts((p) => [...p, { id, ...t }]);
  }, []);
  return (
    <ToastCtx.Provider value={push}>
      <RT.Provider swipeDirection="right" duration={4500}>
        {children}
        {toasts.map((t) => (
          <RT.Root
            key={t.id}
            onOpenChange={(o) => !o && setToasts((p) => p.filter((x) => x.id !== t.id))}
            className={cn(
              "glass rounded-xl p-4 pr-10 min-w-[280px] max-w-sm shadow-glass",
              "data-[state=open]:animate-in data-[state=open]:slide-in-from-right",
              "data-[state=closed]:animate-out data-[state=closed]:slide-out-to-right",
              t.variant === "error" && "border-red-500/40",
              t.variant === "success" && "border-emerald-500/40"
            )}
          >
            <RT.Title className="text-sm font-semibold">{t.title}</RT.Title>
            {t.description && <RT.Description className="mt-1 text-xs text-muted">{t.description}</RT.Description>}
            <RT.Close className="absolute right-2 top-2 p-1 text-muted hover:text-foreground">
              <X className="h-4 w-4" />
            </RT.Close>
          </RT.Root>
        ))}
        <RT.Viewport className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 outline-none" />
      </RT.Provider>
    </ToastCtx.Provider>
  );
}
