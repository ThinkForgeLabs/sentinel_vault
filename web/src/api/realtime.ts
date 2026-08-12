import { api } from "./client";
import type { AlertSettings, RealtimeStatus } from "@/types/realtime";

export const realtimeApi = {
  status: () => api.get<RealtimeStatus>("/realtime/status"),

  getSettings: () => api.get<AlertSettings>("/realtime/settings"),

  updateSettings: (data: Partial<AlertSettings>) =>
    api.put<AlertSettings>("/realtime/settings", data),
};
