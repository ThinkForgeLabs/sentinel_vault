// api/events.ts

import { api } from "./client";
import type { CameraEvent, EventFilters, EventStats } from "@/types/event";

export const eventsApi = {
  list: (filters?: EventFilters) => {
    const params: Record<string, string> = {};
    if (filters?.camera_id) params.camera_id = filters.camera_id;
    if (filters?.event_type) params.event_type = filters.event_type;
    if (filters?.importance) params.importance = filters.importance;
    if (filters?.page) params.page = String(filters.page);
    return api.get<CameraEvent[]>("/events", params);
  },

  get: (id: string) =>
    api.get<CameraEvent>(`/events/${id}`),

  stats: () =>
    api.get<EventStats>("/events/stats"),

  updateReview: (id: string, status: string) =>
    api.patch<CameraEvent>(`/events/${id}`, { review_status: status }),

  delete: (id: string) =>
    api.delete<void>(`/events/${id}`),
};