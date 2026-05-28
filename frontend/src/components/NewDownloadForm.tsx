import { useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { useCreateJob } from "@/hooks/useJobs";
import { useToast } from "./Toaster";
import type { MediaType, Quality } from "@/lib/api";

const YT_RE = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be|m\.youtube\.com|music\.youtube\.com)\//;

export function NewDownloadForm({ onCreated }: { onCreated?: () => void }) {
  const [url, setUrl] = useState("");
  const [mediaType, setMediaType] = useState<MediaType>("video");
  const [quality, setQuality] = useState<Quality>("best");
  const toast = useToast();
  const create = useCreateJob();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!YT_RE.test(url)) {
      toast({ title: "That URL doesn't look right", description: "Paste a YouTube link.", variant: "error" });
      return;
    }
    try {
      await create.mutateAsync({ url, media_type: mediaType, quality: mediaType === "audio" ? "audio" : quality });
      toast({ title: "Queued", description: "Your download is on the way.", variant: "success" });
      setUrl("");
      onCreated?.();
    } catch (err: any) {
      toast({ title: "Couldn't queue download", description: String(err?.message ?? err), variant: "error" });
    }
  };

  return (
    <Card>
      <CardContent className="space-y-4">
        <form onSubmit={submit} className="grid gap-3 md:grid-cols-[1fr_180px_180px_auto]">
          <Input
            placeholder="Paste a YouTube URL you own or are authorized to archive"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            autoFocus
          />
          <Select value={mediaType} onValueChange={(v) => setMediaType(v as MediaType)}>
            <SelectTrigger><SelectValue placeholder="Type" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="video">Video (MP4)</SelectItem>
              <SelectItem value="audio">Audio (MP3)</SelectItem>
            </SelectContent>
          </Select>
          <Select
            value={mediaType === "audio" ? "audio" : quality}
            onValueChange={(v) => setQuality(v as Quality)}
            disabled={mediaType === "audio"}
          >
            <SelectTrigger><SelectValue placeholder="Quality" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="best">Best available</SelectItem>
              <SelectItem value="1080p">1080p</SelectItem>
              <SelectItem value="720p">720p</SelectItem>
              <SelectItem value="audio">Audio only</SelectItem>
            </SelectContent>
          </Select>
          <Button type="submit" disabled={create.isPending || !url}>
            {create.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            Archive
          </Button>
        </form>
        <p className="text-[11px] text-muted">
          Only archive content you own or have permission to archive. NeuroArchive is for personal use.
        </p>
      </CardContent>
    </Card>
  );
}
