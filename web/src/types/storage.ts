export interface CameraBreakdown {
  camera_id: string;
  camera_name: string;
  retention_days: number;
  recording_count: number;
  size_bytes: number;
}

export interface StorageStats {
  disk_total_bytes: number;
  disk_used_bytes: number;
  disk_free_bytes: number;
  disk_usage_percent: number;
  recordings_total_bytes: number;
  recordings_count: number;
  recordings_total_duration_seconds: number;
  max_storage_gb: number | null;
  storage_warning_percent: number;
  storage_warning_active: boolean;
  per_camera: CameraBreakdown[];
}

export interface StorageSettingsPayload {
  max_storage_gb: number | null;
  storage_warning_percent: number;
}

export interface CleanupResult {
  expired_deleted: number;
  cap_deleted: number;
  orphans_removed: number;
  empty_dirs_removed: number;
}