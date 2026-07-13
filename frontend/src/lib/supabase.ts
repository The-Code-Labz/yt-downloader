import { createClient } from "@supabase/supabase-js";
import { runtimeEnv } from "./runtime-env";

const url = runtimeEnv.SUPABASE_URL;
const anon = runtimeEnv.SUPABASE_ANON_KEY;

export const supabase = createClient(url, anon, {
  auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
});
