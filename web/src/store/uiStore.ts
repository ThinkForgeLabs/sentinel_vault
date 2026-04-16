import { create } from "zustand";

interface Toast {
  id: string;
  title: string;
  description?: string;
  variant?: "default" | "success" | "error" | "warning";
}

interface UiState {
  sidebarOpen: boolean;
  toasts: Toast[];
  toggleSidebar: () => void;
  closeSidebar: () => void;
  addToast: (toast: Omit<Toast, "id">) => void;
  removeToast: (id: string) => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: false,
  toasts: [],

  toggleSidebar: () =>
    set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  closeSidebar: () =>
    set({ sidebarOpen: false }),

  addToast: (toast) => {
    const id = Date.now().toString(36);
    set((s) => ({ toasts: [...s.toasts, { ...toast, id }] }));
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, 4000);
  },

  removeToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));