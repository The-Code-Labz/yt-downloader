import { Inbox } from "lucide-react";

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="glass rounded-2xl p-12 text-center">
      <div className="mx-auto h-12 w-12 rounded-full bg-surface2 grid place-items-center mb-4 text-muted">
        <Inbox className="h-5 w-5" />
      </div>
      <h2 className="text-base font-semibold">{title}</h2>
      {hint && <p className="text-sm text-muted mt-1">{hint}</p>}
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="glass rounded-2xl overflow-hidden">
      <div className="aspect-video skeleton" />
      <div className="p-4 space-y-3">
        <div className="h-4 w-3/4 skeleton rounded" />
        <div className="h-3 w-1/3 skeleton rounded" />
        <div className="h-8 w-full skeleton rounded" />
      </div>
    </div>
  );
}
