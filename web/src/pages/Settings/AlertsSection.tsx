import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";
import { realtimeApi } from "@/api/realtime";
import { useRealtimeStore } from "@/store/realtimeStore";
import { useUiStore } from "@/store/uiStore";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/cn";
import type { AlertSettings } from "@/types/realtime";
import type { Importance } from "@/types/common";

const IMPORTANCE_LEVELS: Importance[] = ["low", "medium", "high", "critical"];

export function AlertsSection() {
  const addToast = useUiStore((s) => s.addToast);
  const setStoreSettings = useRealtimeStore((s) => s.setSettings);
  const connected = useRealtimeStore((s) => s.connected);
  const isOwner = useAuth().user?.role === "owner";

  const [settings, setSettings] = useState<AlertSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    realtimeApi
      .getSettings()
      .then((s) => {
        setSettings(s);
        setStoreSettings(s);
      })
      .catch(() => setSettings(null))
      .finally(() => setLoading(false));
  }, [setStoreSettings]);

  const update = (patch: Partial<AlertSettings>) =>
    setSettings((prev) => (prev ? { ...prev, ...patch } : prev));

  const handleSave = async () => {
    if (!settings) return;
    setSaving(true);
    try {
      const updated = await realtimeApi.updateSettings(settings);
      setSettings(updated);
      setStoreSettings(updated);
      addToast({ title: "Alert settings saved", variant: "success" });
    } catch (err) {
      addToast({
        title: "Failed to save alert settings",
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

  if (!settings) {
    return <p className="text-sm text-gray-500">Unable to load alert settings.</p>;
  }

  return (
    <div className="space-y-5">
      <div
        className={cn(
          "flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-medium",
          connected
            ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
            : "border-red-500/30 bg-red-500/10 text-red-400"
        )}
      >
        <span className={cn("h-1.5 w-1.5 rounded-full", connected ? "bg-emerald-400" : "bg-red-400")} />
        Realtime channel is {connected ? "connected" : "offline"}
      </div>

      <div className="flex items-center justify-between rounded-lg border border-border bg-elevated px-4 py-3">
        <div>
          <p className="text-sm font-medium">In-app / local notifications</p>
          <p className="text-xs text-gray-500">Toasts, sound, and desktop notifications for new events</p>
        </div>
        <button
          onClick={() => update({ websocket_enabled: !settings.websocket_enabled })}
          disabled={!isOwner}
          className={cn(
            "h-6 w-11 flex-shrink-0 rounded-full transition-colors disabled:opacity-40",
            settings.websocket_enabled ? "bg-cyan-500" : "bg-gray-700"
          )}
        >
          <span
            className={cn(
              "block h-5 w-5 translate-y-0.5 rounded-full bg-white transition-transform",
              settings.websocket_enabled ? "translate-x-5" : "translate-x-0.5"
            )}
          />
        </button>
      </div>

      <div className="flex items-center justify-between rounded-lg border border-border bg-elevated px-4 py-3">
        <div>
          <p className="text-sm font-medium">Local network broadcast</p>
          <p className="text-xs text-gray-500">
            Sends a UDP alert on the LAN so other devices on your network can react
          </p>
        </div>
        <button
          onClick={() => update({ lan_broadcast_enabled: !settings.lan_broadcast_enabled })}
          disabled={!isOwner}
          className={cn(
            "h-6 w-11 flex-shrink-0 rounded-full transition-colors disabled:opacity-40",
            settings.lan_broadcast_enabled ? "bg-cyan-500" : "bg-gray-700"
          )}
        >
          <span
            className={cn(
              "block h-5 w-5 translate-y-0.5 rounded-full bg-white transition-transform",
              settings.lan_broadcast_enabled ? "translate-x-5" : "translate-x-0.5"
            )}
          />
        </button>
      </div>

      {settings.lan_broadcast_enabled && (
        <Input
          label="Broadcast Port"
          type="number"
          min={1024}
          max={65535}
          value={settings.lan_broadcast_port}
          disabled={!isOwner}
          onChange={(e) => update({ lan_broadcast_port: Number(e.target.value) })}
          hint="UDP port used for the local network broadcast (1024-65535)"
        />
      )}

      <div>
        <label className="block text-xs font-semibold text-gray-400 mb-1.5">
          Minimum importance to alert on
        </label>
        <div className="flex gap-2">
          {IMPORTANCE_LEVELS.map((level) => (
            <button
              key={level}
              type="button"
              disabled={!isOwner}
              onClick={() => update({ min_importance: level })}
              className={cn(
                "flex-1 rounded-lg border px-3 py-2 text-xs font-medium capitalize transition disabled:opacity-40",
                settings.min_importance === level
                  ? "border-cyan-400 bg-accent/10 text-cyan-400"
                  : "border-border text-gray-400 hover:text-white"
              )}
            >
              {level}
            </button>
          ))}
        </div>
      </div>

      {isOwner ? (
        <div className="pt-2">
          <Button onClick={handleSave} loading={saving}>
            Save Changes
          </Button>
        </div>
      ) : (
        <p className="text-xs text-gray-500">Only owners can change alert settings.</p>
      )}
    </div>
  );
}
