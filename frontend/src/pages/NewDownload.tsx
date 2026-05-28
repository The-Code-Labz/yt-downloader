import { useNavigate } from "react-router-dom";
import { NewDownloadForm } from "@/components/NewDownloadForm";
import { TopBar } from "@/components/TopBar";
import { useState } from "react";

export default function NewDownload() {
  const nav = useNavigate();
  const [q, setQ] = useState("");
  return (
    <div className="flex-1 min-w-0">
      <TopBar query={q} onQuery={setQ} />
      <main className="px-5 md:px-8 py-8 max-w-3xl">
        <h1 className="text-2xl font-semibold tracking-tight">New Download</h1>
        <p className="text-sm text-muted mt-1 mb-6">Queue a video or audio extraction.</p>
        <NewDownloadForm onCreated={() => nav("/")} />
      </main>
    </div>
  );
}
