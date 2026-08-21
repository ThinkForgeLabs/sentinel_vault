import type { Importance, ReviewStatus } from "./common";

export interface CameraEvent {
  id: string;
  camera_id: string | null;
  device_id: string | null;
  event_type: string;
  subtype: string | null;
  started_at: string;
  ended_at: string | null;
  confidence: number;
  importance: Importance;
  thumbnail_path: string | null;
  clip_path: string | null;
  clip_duration_seconds: number | null;
  alerted: boolean;
  review_status: ReviewStatus;
  created_at: string;
}

export interface EventStats {
  total_today: number;
  by_type: Record<string, number>;
  alerted_count: number;
}

export interface EventFilters {
  camera_id?: string;
  device_id?: string;
  event_type?: string;
  importance?: Importance;
  page?: number;
}