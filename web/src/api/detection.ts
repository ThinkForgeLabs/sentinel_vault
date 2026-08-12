import { api } from "./client";
import type { MotionSettings, MotionSettingsUpdate, MotionStatus } from "@/types/detection";

export const detectionApi = {
  getSettings: (cameraId: string) =>
    api.get<MotionSettings>(`/detection/${cameraId}/settings`),

  updateSettings: (cameraId: string, data: MotionSettingsUpdate) =>
    api.put<MotionSettings>(`/detection/${cameraId}/settings`, data),

  status: (cameraId: string) =>
    api.get<MotionStatus>(`/detection/${cameraId}/status`),
};
