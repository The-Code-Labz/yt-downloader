import {
  Play, Download as DownloadIcon, Trash2, Link2, RefreshCw,
  Music, Film, AlertTriangle, Loader2, CheckCircle2,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useToast } from "./Toaster";
import { useDeleteJob, useCreateJob } from "@/hooks/useJobs";
import { useJobStream } from "@/hooks/useJobStream";
import { formatBytes, formatDuration, relativeTime } from "@/lib/utils";
import type { Download } from "@/lib/api";

const ACTIVE = new Set(["queued", "downloading", "processing", "uploading"]);

export function DownloadCard({ d }: { d: Download }) {
  const toast = useToast();
  const remove = useDeleteJob();
  const recreate = useCreateJob();
  // Live progress while the job is active
  useJobStream(ACTIVE.has(d.status) ? d.id : null);

  const isAudio = d.media_type === "audio";
  const playable = d.status === "completed" && d.signed_url;

  const onDelete = async () => {
    if (!confirm(`Delete "${d.title ?? d.source_url}"? The file in R2 will also be removed.`)) return;
    try {
      await remove.mutateAsync(d.id);
      toast({ title: "Deleted", variant: "success" });
    } catch (e: any) {
      toast({ title: "Delete failed", description: String(e?.message ?? e), variant: "error" });
    }
  };

  const onRedownload = async () => {
    try {
      await recreate.mutateAsync({ url: d.source_url, media_type: d.media_type, quality: d.quality });
      toast({ title: "Re-queued", variant: "success" });
    } catch (e: any) {
      toast({ title: "Re-download failed", description: String(e?.message ?? e), variant: "error" });
    }
  };

  const copyLink = async () => {
    if (!d.signed_url) return;
    await navigator.clipboard.writeText(d.signed_url);
    toast({ title: "Link copied", description: "Signed URL is on your clipboard." });
  };

  return (
    <Card className="overflow-hidden group transition hover:translate-y-[-2px] hover:shadow-glass">
      <div className="relative aspect-video bg-surface2">
        {d.thumbnail ? (
          <img
            src={d.thumbnail}
            alt={d.title ?? ""}
            className="h-full w-full object-cover opacity-90 group-hover:opacity-100 transition"
            loading="lazy"
          />
        ) : (
          <div className="h-full w-full grid place-items-center text-muted">
            {isAudio ? <Music className="h-10 w-10" /> : <Film className="h-10 w-10" />}
          </div>
        )}
        <div className="absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-black/80 to-transparent" />
        <div className="absolute left-3 top-3 flex gap-1.5">
          <Badge variant={isAudio ? "audio" : "video"}>
            {isAudio ? <><Music className="h-3 w-3" /> mp3</> : <><Film className="h-3 w-3" /> mp4</>}
          </Badge>
          <Badge variant="status">{d.quality}</Badge>
        </div>
        {d.duration ? (
          <span className="absolute right-3 top-3 rounded-md bg-black/60 px-1.5 py-0.5 text-[11px] font-medium text-white/90 tabular-nums">
            {formatDuration(d.duration)}
          </span>
        ) : null}
        <StatusOverlay status={d.status} progress={d.progress} />
      </div>

      <div className="p-4 space-y-3">
        <div className="space-y-1">
          <h3 className="line-clamp-2 text-sm font-semibold leading-snug">
            {d.title ?? <span className="text-muted">Fetching title…</span>}
          </h3>
          <p className="text-[11px] text-muted">
            {relativeTime(d.created_at)} · {formatBytes(d.bytes)}
          </p>
        </div>

        {ACTIVE.has(d.status) && (
          <div className="space-y-1.5">
            <Progress value={d.progress} />
            <div className="flex justify-between text-[11px] text-muted">
              <span className="capitalize">{d.status}</span>
              <span className="tabular-nums">{Math.round(d.progress)}%</span>
            </div>
          </div>
        )}

        {d.status === "failed" && (
          <p className="text-xs text-red-300 line-clamp-2">{d.error ?? "Unknown error"}</p>
        )}

        <div className="flex flex-wrap gap-2 pt-1">
          <Button size="sm" disabled={!playable} asChild={!!playable}>
            {playable ? (
              <a href={d.signed_url!} target="_blank" rel="noreferrer">
                <Play className="h-4 w-4" /> Stream
              </a>
            ) : (
              <span><Play className="h-4 w-4" /> Stream</span>
            )}
          </Button>
          <Button size="sm" variant="outline" disabled={!playable} asChild={!!playable}>
            {playable ? (
              <a href={d.signed_url!} download>
                <DownloadIcon className="h-4 w-4" /> Save
              </a>
            ) : (
              <span><DownloadIcon className="h-4 w-4" /> Save</span>
            )}
          </Button>
          <Button size="sm" variant="ghost" disabled={!playable} onClick={copyLink}>
            <Link2 className="h-4 w-4" /> Copy link
          </Button>
          <Button size="sm" variant="ghost" onClick={onRedownload}>
            <RefreshCw className="h-4 w-4" /> Re-download
          </Button>
          <Button size="sm" variant="ghost" className="text-red-300 hover:text-red-200 ml-auto" onClick={onDelete}>
            <Trash2 className="h-4 w-4" /> Delete
          </Button>
        </div>
      </div>
    </Card>
  );
}

function StatusOverlay({ status, progress }: { status: Download["status"]; progress: number }) {
  if (status === "completed") {
    return (
      <div className="absolute right-3 bottom-3 inline-flex items-center gap-1.5 rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-[11px] font-medium text-emerald-300 border border-emerald-500/30">
        <CheckCircle2 className="h-3 w-3" /> Ready
      </div>
    );
  }
  if (status === "failed") {
    return (
      <div className="absolute right-3 bottom-3 inline-flex items-center gap-1.5 rounded-full bg-red-500/15 px-2.5 py-0.5 text-[11px] font-medium text-red-300 border border-red-500/30">
        <AlertTriangle className="h-3 w-3" /> Failed
      </div>
    );
  }
  if (ACTIVE.has(status)) {
    return (
      <div className="absolute right-3 bottom-3 inline-flex items-center gap-1.5 rounded-full bg-black/60 px-2.5 py-0.5 text-[11px] font-medium text-white/90 border border-white/10">
        <Loader2 className="h-3 w-3 animate-spin" /> {Math.round(progress)}%
      </div>
    );
  }
  return null;
}
