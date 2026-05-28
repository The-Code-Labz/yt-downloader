import { useEffect, useState } from "react";
import { TopBar } from "@/components/TopBar";
import { Card, CardContent } from "@/components/ui/card";
import { supabase } from "@/lib/supabase";

export default function Settings() {
  const [email, setEmail] = useState<string | null>(null);
  const [q, setQ] = useState("");
  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => setEmail(data.user?.email ?? null));
  }, []);

  return (
    <div className="flex-1 min-w-0">
      <TopBar query={q} onQuery={setQ} />
      <main className="px-5 md:px-8 py-8 max-w-3xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
          <p className="text-sm text-muted mt-1">Your environment and account.</p>
        </div>
        <Card>
          <CardContent className="space-y-3 text-sm">
            <Row label="Signed in as" value={email ?? "—"} />
            <Row label="API endpoint" value={import.meta.env.VITE_API_URL as string} mono />
            <Row label="Supabase project" value={import.meta.env.VITE_SUPABASE_URL as string} mono />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="text-sm text-muted leading-relaxed">
            <p className="font-medium text-foreground mb-1">Legal & Acceptable Use</p>
            NeuroArchive is intended for personal archival of content you own the rights to,
            Creative Commons material, or content you have explicit permission to archive.
            Downloading copyrighted content you don't own may violate YouTube's Terms of Service
            and copyright law. You are solely responsible for how you use this software.
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-border/60 last:border-0 py-2.5">
      <span className="text-muted">{label}</span>
      <span className={mono ? "font-mono text-xs" : ""}>{value}</span>
    </div>
  );
}
