import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { TopBar } from "@/components/TopBar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/Toaster";

const API_URL = (import.meta.env.VITE_API_URL as string) || "https://api.example.com";

const ENDPOINTS = [
  { method: "POST", path: "/agent/download", desc: "Start a download job (same body as POST /download)." },
  { method: "GET", path: "/agent/jobs", desc: "List agent-owned jobs." },
  { method: "GET", path: "/agent/job/{id}", desc: "Get a job, with signed_url once completed." },
  { method: "GET", path: "/agent/job/{id}/file", desc: "302-redirects to a fresh signed R2 URL (ready for curl -L)." },
  { method: "DELETE", path: "/agent/job/{id}", desc: "Delete a job and its R2 object." },
] as const;

const METHOD_COLORS: Record<string, string> = {
  POST: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  GET: "bg-blue-500/15 text-blue-300 border-blue-500/30",
  DELETE: "bg-red-500/15 text-red-300 border-red-500/30",
};

const curlExample = `# Start it
job=$(curl -s -X POST "${API_URL}/agent/download" \\
  -H "X-Agent-Key: $AGENT_API_KEY" -H "Content-Type: application/json" \\
  -d '{"url":"https://www.youtube.com/watch?v=...","media_type":"video","quality":"best"}')
id=$(echo "$job" | jq -r .id)

# Poll until completed, then pull it
until [ "$(curl -s "${API_URL}/agent/job/$id" -H "X-Agent-Key: $AGENT_API_KEY" | jq -r .status)" = completed ]; do sleep 5; done
curl -L "${API_URL}/agent/job/$id/file" -H "X-Agent-Key: $AGENT_API_KEY" -o out.mp4`;

const requestBodyExample = `{
  "url": "https://www.youtube.com/watch?v=...",
  "media_type": "video",   // "video" | "audio"
  "quality": "best"        // "best" | "1080p" | "720p" | "audio"
}`;

function markdown(): string {
  const rows = ENDPOINTS.map(
    (e) => `| ${e.method} | \`${e.path}\` | ${e.desc} |`
  ).join("\n");
  return `## Agent API

Base URL: \`${API_URL}\`
Auth: header \`X-Agent-Key: <AGENT_API_KEY>\` on every request. Missing/unconfigured key -> 404. Wrong key -> 401.

| Method | Path | Description |
| --- | --- | --- |
${rows}

### Request body (POST /agent/download)

\`\`\`json
${requestBodyExample}
\`\`\`

### Example

\`\`\`bash
${curlExample}
\`\`\`
`;
}

function CopyButton({ text, label = "Copy" }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  const toast = useToast();
  return (
    <Button
      variant="outline"
      size="sm"
      onClick={async () => {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        toast({ title: "Copied", description: `${label} copied to clipboard.` });
        setTimeout(() => setCopied(false), 1500);
      }}
    >
      {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
      {copied ? "Copied" : label}
    </Button>
  );
}

export default function Docs() {
  const [q, setQ] = useState("");

  return (
    <div className="flex-1 min-w-0">
      <TopBar query={q} onQuery={setQ} />
      <main className="px-5 md:px-8 py-8 max-w-3xl space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Agent API</h1>
            <p className="text-sm text-muted mt-1">
              Let an automated agent start downloads and pull finished files without a
              Supabase login — authed with a shared secret instead of a user JWT.
            </p>
          </div>
          <CopyButton text={markdown()} label="Copy as Markdown" />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Setup</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted leading-relaxed">
            <p>
              1. Create one dedicated Supabase auth user to own agent-created jobs — every
              row in <code className="text-foreground">downloads</code> needs a real{" "}
              <code className="text-foreground">user_id</code> FK, even via the service-role
              key. Copy its UUID.
            </p>
            <p>
              2. On the deployed backend, set{" "}
              <code className="text-foreground">AGENT_API_KEY</code> (random secret) and{" "}
              <code className="text-foreground">AGENT_USER_ID</code> (the UUID from step 1),
              then redeploy.
            </p>
            <p>
              3. Leaving either value unset 404s every <code className="text-foreground">/agent/*</code>{" "}
              route — same behavior as the unconfigured admin-cookies endpoint.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Authentication</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted">
            Every request requires header{" "}
            <code className="text-foreground font-mono text-xs bg-surface2 px-1.5 py-0.5 rounded">
              X-Agent-Key: &lt;AGENT_API_KEY&gt;
            </code>
            . No key configured server-side → 404. Wrong key → 401.
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Endpoints</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-border/60">
              {ENDPOINTS.map((e) => (
                <div key={e.method + e.path} className="flex items-start gap-3 px-5 py-3 text-sm">
                  <Badge className={`${METHOD_COLORS[e.method]} shrink-0 w-16 justify-center`}>
                    {e.method}
                  </Badge>
                  <div className="min-w-0">
                    <div className="font-mono text-xs text-foreground">{e.path}</div>
                    <div className="text-muted mt-0.5">{e.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Request body — POST /agent/download</CardTitle>
            <CopyButton text={requestBodyExample} label="Copy" />
          </CardHeader>
          <CardContent>
            <pre className="text-xs font-mono bg-surface2 rounded-lg p-4 overflow-x-auto">
              {requestBodyExample}
            </pre>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Example — start, poll, pull</CardTitle>
            <CopyButton text={curlExample} label="Copy" />
          </CardHeader>
          <CardContent>
            <pre className="text-xs font-mono bg-surface2 rounded-lg p-4 overflow-x-auto whitespace-pre-wrap">
              {curlExample}
            </pre>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
