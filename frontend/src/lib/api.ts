import { supabase } from "./supabase";
import { runtimeEnv } from "./runtime-env";

const API_URL = runtimeEnv.API_URL;

export type MediaType = "audio" | "video";
export type Quality = "best" | "1080p" | "720p" | "audio";
export type JobStatus =
  | "queued" | "downloading" | "processing" | "uploading"
  | "completed" | "failed" | "deleted";

export interface Download {
  id: string;
  user_id: string;
  source_url: string;
  title: string | null;
  thumbnail: string | null;
  duration: number | null;
  media_type: MediaType;
  quality: Quality;
  status: JobStatus;
  progress: number;
  error: string | null;
  r2_key: string | null;
  public_url: string | null;
  signed_url: string | null;
  bytes: number | null;
  created_at: string;
  updated_at: string;
}

async function authHeaders(): Promise<HeadersInit> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  return token
    ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
    : { "Content-Type": "application/json" };
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = await authHeaders();
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { ...headers, ...(init.headers || {}) },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText} ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  list: () => request<Download[]>("/jobs"),
  get: (id: string) => request<Download>(`/job/${id}`),
  create: (body: { url: string; media_type: MediaType; quality: Quality }) =>
    request<Download>("/download", { method: "POST", body: JSON.stringify(body) }),
  remove: (id: string) =>
    request<void>(`/job/${id}`, { method: "DELETE" }),
};

export function wsUrl(jobId: string, token: string): string {
  const base = API_URL.replace(/^http/, "ws");
  return `${base}/ws/jobs/${jobId}?token=${encodeURIComponent(token)}`;
}
