import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { camerasApi } from "@/api/cameras";
import { useUiStore } from "@/store/uiStore";
import { Usb, Globe, Search, CheckCircle, XCircle, Monitor } from "lucide-react";
import type { CameraCreate, DiscoveredDevice } from "@/types/camera";

type SourceMode = "usb" | "rtsp";

interface CameraFormProps {
  onSuccess: () => void;
  onCancel: () => void;
}

export function CameraForm({ onSuccess, onCancel }: CameraFormProps) {
  const addToast = useUiStore((s) => s.addToast);
  const [mode, setMode] = useState<SourceMode>("usb");
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [testing, setTesting] = useState(false);
  const [devices, setDevices] = useState<DiscoveredDevice[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<DiscoveredDevice | null>(null);
  const [form, setForm] = useState<CameraCreate>({
    name: "",
    location_label: "",
    rtsp_url: "",
    record_enabled: true,
    ai_enabled: false,
    retention_days: 14,
  });

  const update = (patch: Partial<CameraCreate>) =>
    setForm((prev) => ({ ...prev, ...patch }));

  const handleScan = async () => {
    setScanning(true);
    setDevices([]);
    setSelectedDevice(null);
    try {
      const found = await camerasApi.discover();
      setDevices(found);
      if (found.length === 0) {
        addToast({ title: "No cameras found", variant: "error" });
      }
    } catch {
      addToast({ title: "Scan failed", variant: "error" });
    } finally {
      setScanning(false);
    }
  };

  const handleSelectDevice = (device: DiscoveredDevice) => {
    setSelectedDevice(device);
    update({
      rtsp_url: device.url,
      name: form.name || device.name,
    });
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      const result = await camerasApi.testConnection(form.rtsp_url);
      addToast({
        title: result.success ? "Connection OK" : "Connection Failed",
        description: result.message,
        variant: result.success ? "success" : "error",
      });
    } catch {
      addToast({ title: "Test failed", variant: "error" });
    } finally {
      setTesting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (mode === "usb" && !selectedDevice) {
      addToast({ title: "Please scan and select a camera", variant: "error" });
      return;
    }
    if (mode === "rtsp" && !form.rtsp_url) {
      addToast({ title: "Please enter an RTSP URL", variant: "error" });
      return;
    }

    setLoading(true);
    try {
      await camerasApi.create(form);
      addToast({ title: "Camera added", variant: "success" });
      onSuccess();
    } catch (err) {
      addToast({
        title: "Failed to add camera",
        description: err instanceof Error ? err.message : undefined,
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* ── Source Mode Toggle ── */}
      <div className="flex gap-2 rounded-xl bg-elevated p-1">
        <button
          type="button"
          onClick={() => {
            setMode("usb");
            setSelectedDevice(null);
            update({ rtsp_url: "" });
          }}
          className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
            mode === "usb"
              ? "bg-cyan-600 text-white shadow"
              : "text-gray-400 hover:text-white"
          }`}
        >
          <Usb size={16} /> USB Camera
        </button>
        <button
          type="button"
          onClick={() => {
            setMode("rtsp");
            setSelectedDevice(null);
            update({ rtsp_url: "" });
          }}
          className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
            mode === "rtsp"
              ? "bg-cyan-600 text-white shadow"
              : "text-gray-400 hover:text-white"
          }`}
        >
          <Globe size={16} /> IP / RTSP
        </button>
      </div>

      {/* ── USB Camera Discovery ── */}
      {mode === "usb" && (
        <div className="space-y-3">
          <Button
            type="button"
            variant="secondary"
            onClick={handleScan}
            loading={scanning}
            className="w-full"
          >
            <Search size={16} /> {scanning ? "Scanning..." : "Scan for Cameras"}
          </Button>

          {devices.length > 0 && (
            <div className="space-y-2">
              {devices.map((device) => (
                <button
                  key={device.index}
                  type="button"
                  onClick={() => device.working && handleSelectDevice(device)}
                  className={`flex w-full items-center gap-3 rounded-xl border p-3 text-left transition ${
                    selectedDevice?.index === device.index
                      ? "border-cyan-500 bg-cyan-500/10"
                      : device.working
                        ? "border-border bg-elevated hover:border-cyan-800 cursor-pointer"
                        : "border-border bg-elevated opacity-50 cursor-not-allowed"
                  }`}
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-black/40">
                    <Monitor size={20} className="text-gray-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold">{device.name}</p>
                    <p className="text-xs text-gray-500">{device.resolution}</p>
                  </div>
                  {device.working ? (
                    <CheckCircle
                      size={18}
                      className={
                        selectedDevice?.index === device.index
                          ? "text-cyan-400"
                          : "text-emerald-400"
                      }
                    />
                  ) : (
                    <XCircle size={18} className="text-red-500" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── RTSP URL Input ── */}
      {mode === "rtsp" && (
        <Input
          label="RTSP URL"
          placeholder="rtsp://192.168.1.100:554/stream"
          value={form.rtsp_url}
          onChange={(e) => update({ rtsp_url: e.target.value })}
          required
        />
      )}

      {/* ── Common Fields ── */}
      <Input
        label="Camera Name"
        placeholder="e.g., Front Door"
        value={form.name}
        onChange={(e) => update({ name: e.target.value })}
        required
      />
      <div className="grid grid-cols-2 gap-3">
        <Input
          label="Location"
          placeholder="Main Entrance"
          value={form.location_label}
          onChange={(e) => update({ location_label: e.target.value })}
        />
        <Input
          label="Retention (days)"
          type="number"
          min={1}
          max={365}
          value={form.retention_days}
          onChange={(e) => update({ retention_days: Number(e.target.value) })}
        />
      </div>

      {/* ── Actions ── */}
      <div className="flex items-center justify-end gap-3 pt-2">
        <Button type="button" variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
        {mode === "rtsp" && (
          <Button type="button" variant="secondary" onClick={handleTest} loading={testing}>
            Test Connection
          </Button>
        )}
        <Button type="submit" loading={loading}>
          Add Camera
        </Button>
      </div>
    </form>
  );
}