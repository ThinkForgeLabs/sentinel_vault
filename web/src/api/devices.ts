import { api } from "./client";
import type { Device, DeviceCreate, DeviceUpdate } from "@/types/device";

export const devicesApi = {
  list: () =>
    api.get<Device[]>("/devices"),

  get: (id: string) =>
    api.get<Device>(`/devices/${id}`),

  create: (data: DeviceCreate) =>
    api.post<Device>("/devices", data),

  update: (id: string, data: DeviceUpdate) =>
    api.put<Device>(`/devices/${id}`, data),

  delete: (id: string) =>
    api.delete(`/devices/${id}`),
};
