import type { Importance } from "./common";

export interface AlertMessage {
  type: string;
  event_id: string | null;
  camera_id: string;
  camera_name: string | null;
  event_type: string;
  subtype: string | null;
  importance: Importance;
  confidence: number;
  started_at: string;
  thumbnail_url: string | null;
  clip_url: string | null;
}

export interface AlertSettings {
  websocket_enabled: boolean;
  lan_broadcast_enabled: boolean;
  lan_broadcast_port: number;
  min_importance: Importance;
}

export interface RealtimeStatus {
  connected_clients: number;
}
