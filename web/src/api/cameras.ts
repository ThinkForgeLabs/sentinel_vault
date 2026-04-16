import { api } from "./client";
import type {
  Camera,
  CameraCreate,
  CameraUpdate,
  DiscoveredDevice,
  TestConnectionResult,
} from "@/types/camera";

export const camerasApi = {
  list: () =>
    api.get<Camera[]>("/cameras"),

  get: (id: string) =>
    api.get<Camera>(`/cameras/${id}`),

  create: (data: CameraCreate) =>
    api.post<Camera>("/cameras", data),

  update: (id: string, data: CameraUpdate) =>
    api.put<Camera>(`/cameras/${id}`, data),

  delete: (id: string) =>
    api.delete(`/cameras/${id}`),

  testConnection: (rtspUrl: string) =>
    api.post<TestConnectionResult>("/cameras/test-connection", { rtsp_url: rtspUrl }),

  discover: () =>
    api.get<DiscoveredDevice[]>("/cameras/discover"),
};