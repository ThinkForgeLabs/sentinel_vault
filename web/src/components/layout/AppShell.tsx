import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { useUiStore } from "@/store/uiStore";
import { X } from "lucide-react";

export function AppShell() {
  const toasts = useUiStore((s) => s.toasts);
  const removeToast = useUiStore((s) => s.removeToast);

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden">
        <Outlet />
      </main>

      {/* Toast container */}
      <div className="fixed right-5 top-5 z-50 flex flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className="flex items-center gap-3 rounded-xl border border-border bg-surface px-4 py-3 shadow-2xl shadow-black/40 animate-fade-in min-w-72"
          >
            <div className="flex-1">
              <p className="text-sm font-semibold">{t.title}</p>
              {t.description && (
                <p className="text-xs text-gray-400 mt-0.5">{t.description}</p>
              )}
            </div>
            <button
              onClick={() => removeToast(t.id)}
              className="text-gray-500 hover:text-white"
            >
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}