import { useState, useRef, useEffect } from "react";
import { Menu, Search, Bell, WifiOff } from "lucide-react";
import { useUiStore } from "@/store/uiStore";
import { useRealtimeStore } from "@/store/realtimeStore";
import { cn } from "@/lib/cn";
import { timeAgo } from "@/lib/date";
import { eventTypeLabel } from "@/lib/format";

interface TopbarProps {
  title: string;
}

const IMPORTANCE_DOT: Record<string, string> = {
  low: "bg-gray-500",
  medium: "bg-cyan-400",
  high: "bg-amber-400",
  critical: "bg-red-500",
};

export function Topbar({ title }: TopbarProps) {
  const toggleSidebar = useUiStore((s) => s.toggleSidebar);
  const connected = useRealtimeStore((s) => s.connected);
  const alerts = useRealtimeStore((s) => s.alerts);
  const unreadCount = useRealtimeStore((s) => s.unreadCount);
  const markAllRead = useRealtimeStore((s) => s.markAllRead);
  const [open, setOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open]);

  const handleToggle = () => {
    setOpen((v) => !v);
    if (!open) markAllRead();
  };

  return (
    <header className="flex h-14 items-center gap-4 border-b border-border bg-surface px-4 lg:px-6">
      <button
        onClick={toggleSidebar}
        className="text-gray-400 lg:hidden hover:text-white transition"
      >
        <Menu size={20} />
      </button>

      <h1 className="flex-1 text-base font-bold">{title}</h1>

      {!connected && (
        <div
          className="flex items-center gap-1.5 rounded-md border border-red-500/30 bg-red-500/10 px-2 py-1 text-xs font-medium text-red-400"
          title="Realtime alert connection is offline"
        >
          <WifiOff size={12} />
          Offline
        </div>
      )}

      <div className="relative hidden md:block">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
        <input
          placeholder="Search events, people..."
          className="w-56 rounded-lg border border-border bg-elevated py-2 pl-9 pr-3 text-xs text-white outline-none placeholder-gray-500 focus:border-accent"
        />
      </div>

      <div className="relative" ref={panelRef}>
        <button
          onClick={handleToggle}
          className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-elevated text-gray-400 transition hover:bg-hover hover:text-white"
        >
          <Bell size={16} />
          {unreadCount > 0 && (
            <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full border-2 border-surface bg-red-500 px-0.5 text-[10px] font-bold leading-none text-white">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </button>

        {open && (
          <div className="absolute right-0 top-11 z-50 w-80 rounded-xl border border-border bg-surface shadow-2xl shadow-black/40 animate-fade-in">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <p className="text-sm font-semibold">Recent Alerts</p>
              <span
                className={cn(
                  "flex items-center gap-1.5 text-xs font-medium",
                  connected ? "text-emerald-400" : "text-red-400"
                )}
              >
                <span
                  className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    connected ? "bg-emerald-400" : "bg-red-400"
                  )}
                />
                {connected ? "Live" : "Offline"}
              </span>
            </div>
            <div className="max-h-80 overflow-y-auto">
              {alerts.length === 0 ? (
                <p className="px-4 py-6 text-center text-xs text-gray-500">
                  No alerts yet.
                </p>
              ) : (
                alerts.map((a, i) => (
                  <div
                    key={`${a.event_id ?? "status"}-${i}`}
                    className="flex items-start gap-2.5 border-b border-border/60 px-4 py-2.5 last:border-b-0"
                  >
                    <span
                      className={cn(
                        "mt-1.5 h-2 w-2 flex-shrink-0 rounded-full",
                        IMPORTANCE_DOT[a.importance] ?? "bg-gray-500"
                      )}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-xs font-semibold">
                        {a.camera_name ?? a.device_name ?? "Unknown source"}
                      </p>
                      <p className="truncate text-xs text-gray-400">
                        {eventTypeLabel(a.event_type)}
                        {a.subtype ? ` · ${a.subtype}` : ""}
                      </p>
                    </div>
                    <span className="flex-shrink-0 text-[11px] text-gray-500">
                      {timeAgo(a.started_at)}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
