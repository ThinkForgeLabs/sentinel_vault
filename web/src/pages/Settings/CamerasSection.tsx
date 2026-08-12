import { useEffect, useState } from "react";
import { Cpu, Activity } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { Badge } from "@/components/ui/Badge";
import { camerasApi } from "@/api/cameras";
import { detectionApi } from "@/api/detection";
import { useUiStore } from "@/store/uiStore";
import { cn } from "@/lib/cn";
import type { Camera } from "@/types/camera";
import type { MotionSettings, MotionStatus } from "@/types/detection";

const PRESETS = [
  {
    id: "quality",
    label: "Full Quality",
    description: "Every frame at full resolution — best for powerful hardware",
    downscale_factor: 1.0,
    frame_skip: 0,
  },
  {
    id: "balanced",
    label: "Balanced",
    description: "Good detection accuracy with reduced CPU usage",
    downscale_factor: 0.75,
    frame_skip: 1,
  },
  {
    id: "low-overhead",
    label: "Low Overhead (Raspberry Pi 5)",
    description: "Downscaled + frame-skipped for constrained hardware",
    downscale_factor: 0.5,
    frame_skip: 2,
  },
] as const;

export function CamerasSection() {
  const addToast = useUiStore((s) => s.addToast);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [settings, setSettings] = useState<MotionSettings | null>(null);
  const [status, setStatus] = useState<MotionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    camerasApi
      .list()
      .then((cams) => {
        setCameras(cams);
        if (cams.length > 0) setSelectedId(cams[0].id);
      })
      .catch(() => setCameras([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    Promise.all([
      detectionApi.getSettings(selectedId),
      detectionApi.status(selectedId).catch(() => null),
    ]).then(([s, st]) => {
      setSettings(s);
      setStatus(st);
    });
  }, [selectedId]);

  const applyPreset = (preset: (typeof PRESETS)[number]) => {
    setSettings((prev) =>
      prev
        ? { ...prev, downscale_factor: preset.downscale_factor, frame_skip: preset.frame_skip }
        : prev
    );
  };

  const handleSave = async () => {
    if (!settings) return;
    setSaving(true);
    try {
      const updated = await detectionApi.updateSettings(selectedId, {
        enabled: settings.enabled,
        threshold: settings.threshold,
        min_contour_area: settings.min_contour_area,
        cooldown_seconds: settings.cooldown_seconds,
        downscale_factor: settings.downscale_factor,
        frame_skip: settings.frame_skip,
      });
      setSettings(updated);
      addToast({ title: "Motion detection settings saved", variant: "success" });
    } catch (err) {
      addToast({
        title: "Failed to save settings",
        description: err instanceof Error ? err.message : undefined,
        variant: "error",
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-24 items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (cameras.length === 0) {
    return <p className="text-sm text-gray-500">No cameras configured yet.</p>;
  }

  return (
    <div className="space-y-5">
      <div>
        <label className="block text-xs font-semibold text-gray-400 mb-1.5">Camera</label>
        <select
          value={selectedId}
          onChange={(e) => setSelectedId(e.target.value)}
          className="w-full rounded-lg border border-border bg-elevated px-3.5 py-2.5 text-sm text-white outline-none focus:border-accent"
        >
          {cameras.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      {status && (
        <div className="flex items-center gap-4 rounded-lg border border-border bg-elevated px-4 py-3 text-xs text-gray-400">
          <span className="flex items-center gap-1.5">
            <Activity size={13} className={status.detector_active ? "text-emerald-400" : "text-gray-500"} />
            {status.detector_active ? "Detector running" : "Detector inactive"}
          </span>
          <span>{status.frames_processed.toLocaleString()} frames processed</span>
        </div>
      )}

      {settings && (
        <>
          <div className="flex items-center justify-between rounded-lg border border-border bg-elevated px-4 py-3">
            <p className="text-sm font-medium">Motion detection enabled</p>
            <button
              onClick={() => setSettings((s) => (s ? { ...s, enabled: !s.enabled } : s))}
              className={cn(
                "h-6 w-11 flex-shrink-0 rounded-full transition-colors",
                settings.enabled ? "bg-cyan-500" : "bg-gray-700"
              )}
            >
              <span
                className={cn(
                  "block h-5 w-5 translate-y-0.5 rounded-full bg-white transition-transform",
                  settings.enabled ? "translate-x-5" : "translate-x-0.5"
                )}
              />
            </button>
          </div>

          <div>
            <label className="mb-2 flex items-center gap-2 text-xs font-semibold text-gray-400">
              <Cpu size={13} /> Performance Preset
            </label>
            <div className="space-y-2">
              {PRESETS.map((p) => {
                const active =
                  settings.downscale_factor === p.downscale_factor &&
                  settings.frame_skip === p.frame_skip;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => applyPreset(p)}
                    className={cn(
                      "flex w-full items-center justify-between rounded-lg border px-3.5 py-2.5 text-left transition",
                      active
                        ? "border-cyan-400 bg-accent/10"
                        : "border-border bg-elevated hover:border-border-lt"
                    )}
                  >
                    <div>
                      <p className="text-sm font-medium">{p.label}</p>
                      <p className="text-xs text-gray-500">{p.description}</p>
                    </div>
                    {active && <Badge variant="accent">Active</Badge>}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-1.5">
                Downscale Factor ({settings.downscale_factor.toFixed(2)}×)
              </label>
              <input
                type="range"
                min={0.25}
                max={1}
                step={0.05}
                value={settings.downscale_factor}
                onChange={(e) =>
                  setSettings((s) => (s ? { ...s, downscale_factor: Number(e.target.value) } : s))
                }
                className="w-full accent-cyan-400"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-1.5">
                Frame Skip ({settings.frame_skip})
              </label>
              <input
                type="range"
                min={0}
                max={10}
                step={1}
                value={settings.frame_skip}
                onChange={(e) =>
                  setSettings((s) => (s ? { ...s, frame_skip: Number(e.target.value) } : s))
                }
                className="w-full accent-cyan-400"
              />
            </div>
          </div>

          <div className="pt-2">
            <Button onClick={handleSave} loading={saving}>
              Save Changes
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
