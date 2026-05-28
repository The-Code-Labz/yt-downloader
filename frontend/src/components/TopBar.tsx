import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { supabase } from "@/lib/supabase";

export function TopBar({ query, onQuery }: { query: string; onQuery: (q: string) => void }) {
  const [email, setEmail] = useState<string | null>(null);
  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => setEmail(data.user?.email ?? null));
  }, []);
  return (
    <header className="sticky top-0 z-10 border-b border-border bg-background/70 backdrop-blur-xl">
      <div className="flex h-14 items-center gap-3 px-5">
        <div className="relative w-full max-w-md">
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted" />
          <input
            value={query}
            onChange={(e) => onQuery(e.target.value)}
            placeholder="Search your archive…"
            className="h-9 w-full rounded-lg border border-border bg-surface pl-9 pr-3 text-sm placeholder:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-ring"
          />
        </div>
        <div className="ml-auto flex items-center gap-2 text-xs text-muted">
          <span className="hidden sm:inline">{email}</span>
          <div className="h-7 w-7 grid place-items-center rounded-full bg-accent/20 text-accent text-[11px] font-semibold uppercase">
            {(email?.[0] ?? "u")}
          </div>
        </div>
      </div>
    </header>
  );
}
