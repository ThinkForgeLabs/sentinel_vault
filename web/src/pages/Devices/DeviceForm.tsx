import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { devicesApi } from "@/api/devices";
import { useUiStore } from "@/store/uiStore";
import type { DeviceCreate, DeviceProtocol, DeviceType } from "@/types/device";

interface DeviceFormProps {
  onSuccess: () => void;
  onCancel: () => void;
}

const DEVICE_TYPES: { value: DeviceType; label: string }[] = [
  { value: "presence_sensor", label: "Presence Sensor" },
  { value: "door_sensor", label: "Door Sensor" },
  { value: "window_sensor", label: "Window Sensor" },
  { value: "doorbell_button", label: "Doorbell Button" },
  { value: "other", label: "Other" },
];

const PROTOCOLS: { value: DeviceProtocol; label: string }[] = [
  { value: "esphome", label: "ESPHome (MQTT)" },
  { value: "zigbee2mqtt", label: "Zigbee2MQTT" },
];

const selectClass =
  "w-full rounded-lg border border-border bg-elevated px-3.5 py-2.5 text-sm text-white outline-none transition-colors focus:border-accent";

export function DeviceForm({ onSuccess, onCancel }: DeviceFormProps) {
  const addToast = useUiStore((s) => s.addToast);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState<DeviceCreate>({
    name: "",
    device_type: "presence_sensor",
    location_label: "",
    protocol: "esphome",
    mqtt_topic: "",
    enabled: true,
  });

  const update = (patch: Partial<DeviceCreate>) =>
    setForm((prev) => ({ ...prev, ...patch }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!form.name || !form.mqtt_topic) {
      addToast({ title: "Please fill in name and MQTT topic", variant: "error" });
      return;
    }

    setLoading(true);
    try {
      await devicesApi.create(form);
      addToast({ title: "Device added", variant: "success" });
      onSuccess();
    } catch (err) {
      addToast({
        title: "Failed to add device",
        description: err instanceof Error ? err.message : undefined,
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <Input
        label="Device Name"
        placeholder="e.g., Front Door Sensor"
        value={form.name}
        onChange={(e) => update({ name: e.target.value })}
        required
      />

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1.5 block text-xs font-semibold text-gray-400">
            Device Type
          </label>
          <select
            className={selectClass}
            value={form.device_type}
            onChange={(e) => update({ device_type: e.target.value as DeviceType })}
          >
            {DEVICE_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1.5 block text-xs font-semibold text-gray-400">
            Protocol
          </label>
          <select
            className={selectClass}
            value={form.protocol}
            onChange={(e) => update({ protocol: e.target.value as DeviceProtocol })}
          >
            {PROTOCOLS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <Input
        label="Location"
        placeholder="Front Door"
        value={form.location_label}
        onChange={(e) => update({ location_label: e.target.value })}
      />

      <Input
        label="MQTT Topic"
        hint="ESPHome status/state topic or Zigbee2MQTT friendly-name topic"
        placeholder="esphome/front-door or zigbee2mqtt/Front Door"
        value={form.mqtt_topic}
        onChange={(e) => update({ mqtt_topic: e.target.value })}
        required
      />

      <div className="flex items-center justify-end gap-3 pt-2">
        <Button type="button" variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          Add Device
        </Button>
      </div>
    </form>
  );
}
