import { useMemo, useState } from "react";
import { useJobs } from "@/hooks/useJobs";
import { NewDownloadForm } from "@/components/NewDownloadForm";
import { DownloadCard } from "@/components/DownloadCard";
import { CardSkeleton, EmptyState } from "@/components/EmptyState";
import { TopBar } from "@/components/TopBar";

export default function Library() {
  const [q, setQ] = useState("");
  const { data, isLoading } = useJobs();

  const filtered = useMemo(() => {
    if (!data) return [];
    const needle = q.trim().toLowerCase();
    if (!needle) return data;
    return data.filter(
      (d) =>
        (d.title ?? "").toLowerCase().includes(needle) ||
        d.source_url.toLowerCase().includes(needle)
    );
  }, [data, q]);

  return (
    <div className="flex-1 min-w-0">
      <TopBar query={q} onQuery={setQ} />
      <main className="px-5 md:px-8 py-8 space-y-8">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Your Archive</h1>
          <p className="text-sm text-muted mt-1">
            Paste a URL to add something new. Everything below lives in your Cloudflare R2 bucket.
          </p>
        </div>

        <NewDownloadForm />

        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)}
          </div>
        ) : !filtered.length ? (
          <EmptyState
            title={q ? "No matches" : "Nothing archived yet"}
            hint={q ? "Try a different search." : "Paste a YouTube URL above to begin."}
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filtered.map((d) => <DownloadCard key={d.id} d={d} />)}
          </div>
        )}
      </main>
    </div>
  );
}
