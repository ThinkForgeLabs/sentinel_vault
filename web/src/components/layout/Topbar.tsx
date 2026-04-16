import { Menu, Search, Bell } from "lucide-react";
import { useUiStore } from "@/store/uiStore";

interface TopbarProps {
  title: string;
}

export function Topbar({ title }: TopbarProps) {
  const toggleSidebar = useUiStore((s) => s.toggleSidebar);

  return (
    <header className="flex h-14 items-center gap-4 border-b border-border bg-surface px-4 lg:px-6">
      <button
        onClick={toggleSidebar}
        className="text-gray-400 lg:hidden hover:text-white transition"
      >
        <Menu size={20} />
      </button>

      <h1 className="flex-1 text-base font-bold">{title}</h1>

      <div className="relative hidden md:block">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
        <input
          placeholder="Search events, people..."
          className="w-56 rounded-lg border border-border bg-elevated py-2 pl-9 pr-3 text-xs text-white outline-none placeholder-gray-500 focus:border-accent"
        />
      </div>

      <button className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-elevated text-gray-400 transition hover:bg-hover hover:text-white">
        <Bell size={16} />
        <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full border-2 border-surface bg-red-500" />
      </button>
    </header>
  );
}