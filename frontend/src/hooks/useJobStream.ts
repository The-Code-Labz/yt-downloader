import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";
import { wsUrl, Download } from "@/lib/api";

/**
 * Subscribes to /ws/jobs/{id} and patches the React Query cache as progress flows in.
 */
export function useJobStream(jobId: string | null | undefined) {
  const qc = useQueryClient();
  useEffect(() => {
    if (!jobId) return;
    let ws: WebSocket | null = null;
    let cancelled = false;

    (async () => {
      const { data } = await supabase.auth.getSession();
      const token = data.session?.access_token;
      if (!token || cancelled) return;
      ws = new WebSocket(wsUrl(jobId, token));
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg.type !== "progress") return;
          qc.setQueryData<Download[]>(["jobs"], (rows) =>
            rows?.map((r) => (r.id === jobId ? { ...r, ...msg } : r))
          );
          if (msg.status === "completed" || msg.status === "failed") {
            qc.invalidateQueries({ queryKey: ["jobs"] });
          }
        } catch {/* ignore */}
      };
    })();

    return () => { cancelled = true; ws?.close(); };
  }, [jobId, qc]);
}
