import { Radar, DoorOpen, PanelTop, Bell, Cpu, Trash2, type LucideIcon } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import type { Device, DeviceType } from "@/types/device";

interface DeviceCardProps {
  device: Device;
  onDelete: (device: Device) => void;
}

const typeIcon: Record<DeviceType, LucideIcon> = {
  presence_sensor: Radar,
  door_sensor: DoorOpen,
  window_sensor: PanelTop,
  doorbell_button: Bell,
  other: Cpu,
};

const typeLabel: Record<DeviceType, string> = {
  presence_sensor: "Presence Sensor",
  door_sensor: "Door Sensor",
  window_sensor: "Window Sensor",
  doorbell_button: "Doorbell Button",
  other: "Other",
};

export function DeviceCard({ device, onDelete }: DeviceCardProps) {
  const isOnline = device.status === "online";
  const Icon = typeIcon[device.device_type] ?? Cpu;

  return (
    <div className="group card p-4 transition hover:border-cyan-800">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-black/40">
            <Icon size={20} className="text-gray-400" />
          </div>
          <div>
            <p className="text-sm font-semibold">{device.name}</p>
            <p className="text-xs text-gray-500">
              {device.location_label || "No location"}
            </p>
          </div>
        </div>
        <button
          onClick={() => onDelete(device)}
          className="rounded-lg p-2 text-gray-500 opacity-0 transition hover:bg-red-500/10 hover:text-red-400 group-hover:opacity-100"
          title="Delete device"
        >
          <Trash2 size={14} />
        </button>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-1.5">
        <Badge variant={isOnline ? "green" : "muted"}>
          <span
            className={`h-1.5 w-1.5 rounded-full ${isOnline ? "bg-emerald-400" : "bg-gray-500"}`}
          />
          {isOnline ? "Online" : "Offline"}
        </Badge>
        <Badge variant="accent">{typeLabel[device.device_type] ?? device.device_type}</Badge>
        <Badge variant="muted">{device.protocol}</Badge>
        {!device.enabled && <Badge variant="yellow">Disabled</Badge>}
      </div>

      <p className="mt-3 truncate text-xs text-gray-500" title={device.mqtt_topic}>
        {device.mqtt_topic}
      </p>
    </div>
  );
}
