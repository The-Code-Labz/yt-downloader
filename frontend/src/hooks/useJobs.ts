import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, Download } from "@/lib/api";

export function useJobs() {
  return useQuery<Download[]>({
    queryKey: ["jobs"],
    queryFn: api.list,
    refetchInterval: (q) => {
      const data = q.state.data as Download[] | undefined;
      const active = data?.some((d) =>
        ["queued", "downloading", "processing", "uploading"].includes(d.status)
      );
      return active ? 2_000 : false;
    },
  });
}

export function useCreateJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs"] }),
  });
}

export function useDeleteJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.remove,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs"] }),
  });
}
