import { api } from "./client";

export interface PlaybackSegment {
  start: string;
  end: string;
  recording_id: string | null;
  duration_seconds: number;
}

export interface PlaybackAvailability {
  camera_id: string;
  segments: PlaybackSegment[];
}

export interface BatchAvailabilityResponse {
  cameras: Record<string, PlaybackSegment[]>;
}

export interface TimelineEventMarker {
  event_id: string;
  camera_id: string;
  started_at: string;
  ended_at: string | null;
  event_type: string;
  importance: string;
}

export const playbackApi = {
  availability: (cameraId: string, start: string, end: string) =>
    api.get<PlaybackAvailability>("/playback/availability", {
      camera_id: cameraId,
      start,
      end,
    }),

  /** Multicamera wall view — fetch every tile's segments in one round trip. */
  batchAvailability: (cameraIds: string[], start: string, end: string) =>
    api.post<BatchAvailabilityResponse>("/playback/availability/batch", {
      camera_ids: cameraIds,
      start,
      end,
    }),

  /** Frigate-style timeline markers for one or more cameras. */
  timelineEvents: (cameraIds: string[], start: string, end: string) => {
    const url = new URL("http://placeholder/playback/timeline/events");
    cameraIds.forEach((id) => url.searchParams.append("camera_id", id));
    url.searchParams.set("start", start);
    url.searchParams.set("end", end);
    const query = url.search;
    return api.get<{ events: TimelineEventMarker[] }>(`/playback/timeline/events${query}`);
  },

  streamInfo: (cameraId: string) =>
    api.get<{ stream_url: string; codec: string; resolution: string }>(
      `/playback/stream/${cameraId}`
    ),

  /** Path (not a fetch call) for the arbitrary-range clip export — the
   * download itself goes through downloadFile() so it can carry the
   * Authorization header. */
  exportPath: (cameraId: string, start: string, end: string) => {
    const url = new URL("http://placeholder/playback/export");
    url.searchParams.set("camera_id", cameraId);
    url.searchParams.set("start", start);
    url.searchParams.set("end", end);
    return `/playback/export${url.search}`;
  },
};
