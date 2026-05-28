import { useState } from "react";
import { Loader2, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { supabase } from "@/lib/supabase";
import { useToast } from "@/components/Toaster";

export default function Login() {
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [busy, setBusy] = useState<"in" | "up" | "magic" | null>(null);
  const toast = useToast();

  const signIn = async () => {
    setBusy("in");
    const { error } = await supabase.auth.signInWithPassword({ email, password: pw });
    setBusy(null);
    if (error) toast({ title: "Sign-in failed", description: error.message, variant: "error" });
  };
  const signUp = async () => {
    setBusy("up");
    const { error } = await supabase.auth.signUp({ email, password: pw });
    setBusy(null);
    if (error) toast({ title: "Sign-up failed", description: error.message, variant: "error" });
    else toast({ title: "Check your inbox", description: "Confirm your email to finish setup.", variant: "success" });
  };
  const magic = async () => {
    if (!email) return;
    setBusy("magic");
    const { error } = await supabase.auth.signInWithOtp({ email });
    setBusy(null);
    if (error) toast({ title: "Magic link failed", description: error.message, variant: "error" });
    else toast({ title: "Magic link sent", description: "Check your email.", variant: "success" });
  };

  return (
    <div className="min-h-screen grid place-items-center px-6">
      <Card className="w-full max-w-sm">
        <CardContent className="space-y-5">
          <div className="flex items-center gap-2.5">
            <svg className="h-7 w-7 text-accent" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="8" fill="currentColor" opacity="0.15" />
              <path d="M8 22V10l8 8V10l8 12" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <div>
              <h1 className="font-semibold tracking-tight">NeuroArchive</h1>
              <p className="text-xs text-muted">Self-hosted archive for content you own.</p>
            </div>
          </div>
          <div className="space-y-2.5">
            <Input type="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} autoFocus />
            <Input type="password" placeholder="••••••••" value={pw} onChange={(e) => setPw(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Button onClick={signIn} disabled={!!busy || !email || !pw}>
              {busy === "in" ? <Loader2 className="h-4 w-4 animate-spin" /> : null} Sign in
            </Button>
            <Button variant="outline" onClick={signUp} disabled={!!busy || !email || !pw}>
              {busy === "up" ? <Loader2 className="h-4 w-4 animate-spin" /> : null} Create account
            </Button>
          </div>
          <Button variant="ghost" className="w-full" onClick={magic} disabled={!!busy || !email}>
            {busy === "magic" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Mail className="h-4 w-4" />}
            Email me a magic link
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
