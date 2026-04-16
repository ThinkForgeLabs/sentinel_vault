export interface Camera {
  id: string;
  name: string;
  location_label: string;
  status: "online" | "offline";
  record_enabled: boolean;
  ai_enabled: boolean;
  retention_days: number;
  created_at: string;
}

export interface CameraCreate {
  name: string;
  location_label?: string;
  rtsp_url: string;
  record_enabled?: boolean;
  ai_enabled?: boolean;
  retention_days?: number;
}

export interface CameraUpdate {
  name?: string;
  location_label?: string;
  rtsp_url?: string;
  record_enabled?: boolean;
  ai_enabled?: boolean;
  retention_days?: number;
  status?: "online" | "offline";
}

export interface TestConnectionResult {
  success: boolean;
  message: string;
  codec: string | null;
  resolution: string | null;
}

export interface DiscoveredDevice {
  index: number;
  name: string;
  resolution: string;
  working: boolean;
  url: string;
}