/**
 * Runtime environment overrides injected by docker-entrypoint.d/40-env-config.sh
 * into /env-config.js (window.__ENV__) at container start.
 *
 * This lets one published, multi-arch Docker image (built once by CI) be reused
 * by every self-hoster with their own API URL / Supabase project — no rebuild
 * or per-deployment build secrets required. Falls back to the Vite build-time
 * VITE_* vars for `npm run dev` / `vite preview`, where no env-config.js exists.
 */
declare global {
  interface Window {
    __ENV__?: Record<string, string>;
  }
}

function readEnv(runtimeKey: string, viteKey: string, fallback = ""): string {
  const runtimeValue = typeof window !== "undefined" ? window.__ENV__?.[runtimeKey] : undefined;
  if (runtimeValue) return runtimeValue;
  const buildTimeValue = (import.meta.env[viteKey] as string | undefined) || "";
  return buildTimeValue || fallback;
}

export const runtimeEnv = {
  API_URL: readEnv("API_URL", "VITE_API_URL", "http://localhost:8000"),
  SUPABASE_URL: readEnv("SUPABASE_URL", "VITE_SUPABASE_URL"),
  SUPABASE_ANON_KEY: readEnv("SUPABASE_ANON_KEY", "VITE_SUPABASE_ANON_KEY"),
};
