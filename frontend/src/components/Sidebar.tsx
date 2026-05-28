import { NavLink } from "react-router-dom";
import { Library, Plus, Settings, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";
import { supabase } from "@/lib/supabase";

const items = [
  { to: "/", label: "Library", Icon: Library, end: true },
  { to: "/new", label: "New Download", Icon: Plus },
  { to: "/settings", label: "Settings", Icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="hidden md:flex w-60 shrink-0 flex-col border-r border-border bg-surface/40 backdrop-blur-xl">
      <div className="px-5 py-6 flex items-center gap-2.5">
        <Logo className="h-7 w-7 text-accent" />
        <span className="font-semibold tracking-tight">NeuroArchive</span>
      </div>
      <nav className="flex-1 px-2 space-y-1">
        {items.map(({ to, label, Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition",
                isActive
                  ? "bg-surface2 text-foreground shadow-[inset_2px_0_0_0_hsl(2_84%_55%)]"
                  : "text-muted hover:text-foreground hover:bg-surface2/60"
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
      <button
        onClick={() => supabase.auth.signOut()}
        className="m-2 mt-0 flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted hover:text-foreground hover:bg-surface2/60"
      >
        <LogOut className="h-4 w-4" /> Sign out
      </button>
    </aside>
  );
}

function Logo({ className = "" }) {
  return (
    <svg className={className} viewBox="0 0 32 32" fill="none" aria-label="NeuroArchive logo">
      <rect width="32" height="32" rx="8" fill="currentColor" opacity="0.15" />
      <path d="M8 22V10l8 8V10l8 12" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
