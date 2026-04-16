import { api } from "./client";

export interface PlaybackAvailability {
  camera_id: string;
  segments: { start: string; end: string }[];
}

export const playbackApi = {
  availability: (cameraId: string, start: string, end: string) =>
    api.get<PlaybackAvailability>("/playback/availability", {
      camera_id: cameraId,
      start,
      end,
    }),

  streamInfo: (cameraId: string) =>
    api.get<{ stream_url: string; codec: string; resolution: string }>(
      `/playback/stream/${cameraId}`
    ),
};