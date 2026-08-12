export interface MotionSettings {
  camera_id: string;
  enabled: boolean;
  threshold: number;
  min_contour_area: number;
  cooldown_seconds: number;
  /** Low-overhead tuning for constrained hardware (e.g. Raspberry Pi 5). */
  downscale_factor: number;
  frame_skip: number;
}

export interface MotionSettingsUpdate {
  enabled?: boolean;
  threshold?: number;
  min_contour_area?: number;
  cooldown_seconds?: number;
  downscale_factor?: number;
  frame_skip?: number;
}

export interface MotionStatus {
  camera_id: string;
  detector_active: boolean;
  enabled: boolean;
  frames_processed: number;
  last_trigger: string | null;
}
