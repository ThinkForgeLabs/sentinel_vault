export type DeviceType =
  | "presence_sensor"
  | "door_sensor"
  | "window_sensor"
  | "doorbell_button"
  | "other";

export type DeviceProtocol = "esphome" | "zigbee2mqtt";

export interface Device {
  id: string;
  name: string;
  device_type: DeviceType;
  location_label: string;
  protocol: DeviceProtocol;
  mqtt_topic: string;
  status: "online" | "offline";
  enabled: boolean;
  last_seen_at: string | null;
  created_at: string;
}

export interface DeviceCreate {
  name: string;
  device_type: DeviceType;
  location_label?: string;
  protocol: DeviceProtocol;
  mqtt_topic: string;
  enabled?: boolean;
}

export interface DeviceUpdate {
  name?: string;
  device_type?: DeviceType;
  location_label?: string;
  protocol?: DeviceProtocol;
  mqtt_topic?: string;
  enabled?: boolean;
  status?: "online" | "offline";
}
