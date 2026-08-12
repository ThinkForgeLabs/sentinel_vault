import { create } from "zustand";
import type { AlertMessage, AlertSettings } from "@/types/realtime";

interface RealtimeState {
  connected: boolean;
  alerts: AlertMessage[];
  unreadCount: number;
  settings: AlertSettings | null;
  setConnected: (connected: boolean) => void;
  addAlert: (alert: AlertMessage) => void;
  markAllRead: () => void;
  setSettings: (settings: AlertSettings) => void;
}

export const useRealtimeStore = create<RealtimeState>((set) => ({
  connected: false,
  alerts: [],
  unreadCount: 0,
  settings: null,

  setConnected: (connected) => set({ connected }),

  addAlert: (alert) =>
    set((s) => ({
      alerts: [alert, ...s.alerts].slice(0, 50),
      unreadCount: s.unreadCount + 1,
    })),

  markAllRead: () => set({ unreadCount: 0 }),

  setSettings: (settings) => set({ settings }),
}));
