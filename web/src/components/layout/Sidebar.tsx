import { NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  Home,
  Video,
  LayoutGrid,
  Zap,
  Clock,
  Settings,
  ShieldCheck,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/cn";
import { useUiStore } from "@/store/uiStore";
import { useRealtimeStore } from "@/store/realtimeStore";
import { useAuth } from "@/hooks/useAuth";

const items = [
  { to: "/", label: "Home", icon: Home },
  { to: "/cameras", label: "Cameras", icon: Video },
  { to: "/wall", label: "Wall View", icon: LayoutGrid },
  { to: "/events", label: "Events", icon: Zap },
  { to: "/playback", label: "Playback", icon: Clock },
  { to: "/settings", label: "Settings", icon: Settings },
];

function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export function Sidebar() {
  const sidebarOpen = useUiStore((s) => s.sidebarOpen);
  const closeSidebar = useUiStore((s) => s.closeSidebar);
  const connected = useRealtimeStore((s) => s.connected);
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <>
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={closeSidebar}
        />
      )}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-60 flex-col border-r border-border bg-surface transition-transform lg:static lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex items-center gap-3 border-b border-border px-5 py-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-400 to-violet-500 text-white">
            <ShieldCheck size={18} />
          </div>
          <span className="text-base font-bold tracking-tight">
            Sentinel <span className="text-cyan-400">Vault</span>
          </span>
          <span
            className={cn(
              "ml-auto h-2 w-2 rounded-full",
              connected ? "bg-emerald-400 shadow-emerald-400/50 shadow-sm" : "bg-gray-600"
            )}
            title={connected ? "Realtime alerts connected" : "Realtime alerts offline"}
          />
        </div>

        <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 py-3">
          {items.map(({ to, label, icon: Icon }) => {
            const isActive = to === "/" ? location.pathname === "/" : location.pathname.startsWith(to);
            return (
              <NavLink
                key={to}
                to={to}
                onClick={closeSidebar}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3.5 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-accent/10 text-cyan-400"
                    : "text-gray-400 hover:bg-hover hover:text-white"
                )}
              >
                <Icon size={18} />
                {label}
              </NavLink>
            );
          })}
        </nav>

        <div className="border-t border-border px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-cyan-400 text-xs font-bold text-white">
              {user ? initials(user.display_name) : "?"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="truncate text-sm font-semibold">
                {user?.display_name ?? "Unknown"}
              </p>
              <p className="truncate text-xs text-gray-500 capitalize">
                {user?.role ?? ""}
              </p>
            </div>
            <button
              onClick={handleLogout}
              title="Sign out"
              className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg text-gray-500 transition hover:bg-hover hover:text-red-400"
            >
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
