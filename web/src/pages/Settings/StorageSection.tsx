import { useState, useEffect, useCallback } from "react";
import { AlertTriangle, RefreshCw, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/cn";
import { storageApi } from "@/api/storage";
import type { StorageStats } from "@/types/storage";

// ─── Helpers ────────────────────────────────────────────────────────

function formatBytes(bytes: number) {
  if (!bytes || bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let i = 0;
  let val = bytes;
  while (val >= 1024 && i < units.length - 1) {
    val /= 1024;
    i++;
  }
  return `${val.toFixed(1)} ${units[i]}`;
}

function formatDuration(seconds: number) {
  if (!seconds) return "0h 0m";
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h`;
  return `${h}h ${m}m`;
}

// ─── Sub-components ─────────────────────────────────────────────────

function StorageBar({
  label,
  pct,
  detail,
}: {
  label: string;
  pct: number;
  detail: string;
}) {
  const clamped = Math.min(Math.max(pct, 0), 100);
  const color =
    clamped >= 90
      ? "bg-red-500"
      : clamped >= 70
        ? "bg-amber-500"
        : "bg-cyan-400";

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-semibold text-gray-400">{label}</span>
        <span className="text-xs text-gray-500">{pct}%</span>
      </div>
      <div className="h-3 rounded-full bg-gray-700 overflow-hidden mb-1">
        <div
          className={cn("h-full rounded-full transition-all duration-500", color)}
          style={{ width: `${clamped}%` }}
        />
      </div>
      <p className="text-xs text-gray-500">{detail}</p>
    </div>
  );
}

function WarningBanner({ warningPercent }: { warningPercent: number }) {
  return (
    <div className="mb-5 flex items-start gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3">
      <AlertTriangle size={18} className="text-amber-400 shrink-0 mt-0.5" />
      <div>
        <p className="text-sm font-medium text-amber-300">Storage Warning</p>
        <p className="text-xs text-amber-400/80 mt-0.5">
          Usage has passed the {warningPercent}% threshold. Consider increasing
          the limit, reducing retention, or running a cleanup.
        </p>
      </div>
    </div>
  );
}

function CameraTable({ cameras }: { cameras: StorageStats["per_camera"] }) {
  if (!cameras || cameras.length === 0) return null;

  return (
    <div className="mb-5">
      <label className="block text-xs font-semibold text-gray-400 mb-2">
        Per-Camera Breakdown
      </label>
      <div className="rounded-lg border border-border bg-elevated overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-gray-500">
              <th className="px-3 py-2 text-xs font-medium">Camera</th>
              <th className="px-3 py-2 text-xs font-medium">Count</th>
              <th className="px-3 py-2 text-xs font-medium">Size</th>
              <th className="px-3 py-2 text-xs font-medium">Retention</th>
            </tr>
          </thead>
          <tbody>
            {cameras.map((cam) => (
              <tr
                key={cam.camera_id}
                className="border-b border-border/50 last:border-0"
              >
                <td className="px-3 py-2 text-white font-medium">
                  {cam.camera_name}
                </td>
                <td className="px-3 py-2 text-gray-400">
                  {cam.recording_count}
                </td>
                <td className="px-3 py-2 text-gray-400">
                  {formatBytes(cam.size_bytes)}
                </td>
                <td className="px-3 py-2 text-gray-400">
                  {cam.retention_days}d
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Main Section ───────────────────────────────────────────────────

export function StorageSection() {
  const [stats, setStats] = useState<StorageStats | null>(null);
  const [maxGbInput, setMaxGbInput] = useState("");
  const [warnPctInput, setWarnPctInput] = useState(90);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [cleaning, setCleaning] = useState(false);
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error" | "info";
  } | null>(null);

  const showToast = useCallback(
    (message: string, type: "success" | "error" | "info" = "info") => {
      setToast({ message, type });
      setTimeout(() => setToast(null), 5000);
    },
    []
  );

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [storageStats, settings] = await Promise.all([
        storageApi.stats(),
        storageApi.getSettings(),
      ]);
      setStats(storageStats);
      setMaxGbInput(
        settings.max_storage_gb != null ? String(settings.max_storage_gb) : ""
      );
      setWarnPctInput(settings.storage_warning_percent);
    } catch {
      showToast("Failed to load storage data", "error");
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const handleSave = async () => {
    const maxGb = maxGbInput === "" ? null : Number(maxGbInput);
    if (maxGb !== null && (isNaN(maxGb) || maxGb < 0)) {
      showToast("Max storage must be a positive number or empty for unlimited", "error");
      return;
    }
    if (isNaN(warnPctInput) || warnPctInput < 50 || warnPctInput > 99) {
      showToast("Warning threshold must be between 50 and 99", "error");
      return;
    }

    setSaving(true);
    try {
      await storageApi.updateSettings({
        max_storage_gb: maxGb,
        storage_warning_percent: warnPctInput,
      });
      showToast("Storage settings saved", "success");
      await fetchAll();
    } catch {
      showToast("Failed to save settings", "error");
    } finally {
      setSaving(false);
    }
  };

  const handleCleanup = async () => {
    setCleaning(true);
    try {
      const r = await storageApi.cleanup();
      const total =
        r.expired_deleted + r.cap_deleted + r.orphans_removed + r.empty_dirs_removed;
      showToast(
        total > 0
          ? `Cleaned ${r.expired_deleted} expired, ${r.cap_deleted} over cap, ${r.orphans_removed} orphans, ${r.empty_dirs_removed} empty dirs`
          : "Nothing to clean up",
        total > 0 ? "success" : "info"
      );
      await fetchAll();
    } catch {
      showToast("Cleanup failed", "error");
    } finally {
      setCleaning(false);
    }
  };

  // ── Loading state ──

  if (loading) {
    return (
      <div className="flex h-40 items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  // ── Derived values ──

  const diskPct = stats?.disk_usage_percent ?? 0;
  const recBytes = stats?.recordings_total_bytes ?? 0;
  const maxGb = stats?.max_storage_gb;
  const maxBytes = maxGb ? maxGb * 1024 * 1024 * 1024 : null;
  const capPct = maxBytes
    ? Math.round((recBytes / maxBytes) * 1000) / 10
    : null;

  return (
    <>
      {/* Toast */}
      {toast && (
        <div
          className={cn(
            "fixed top-4 right-4 z-50 max-w-sm px-4 py-3 rounded-lg shadow-lg text-white text-sm",
            toast.type === "success" && "bg-green-600",
            toast.type === "error" && "bg-red-600",
            toast.type === "info" && "bg-cyan-600"
          )}
        >
          {toast.message}
        </div>
      )}

      {/* Warning */}
      {stats?.storage_warning_active && (
        <WarningBanner warningPercent={stats.storage_warning_percent} />
      )}

      {/* Overview cards */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        <div className="rounded-lg border border-border bg-elevated p-3">
          <p className="text-xs text-gray-500 uppercase tracking-wide">
            Disk Total
          </p>
          <p className="text-lg font-bold text-white mt-0.5">
            {formatBytes(stats?.disk_total_bytes ?? 0)}
          </p>
          <p className="text-xs text-gray-500">
            {formatBytes(stats?.disk_free_bytes ?? 0)} free
          </p>
        </div>
        <div className="rounded-lg border border-border bg-elevated p-3">
          <p className="text-xs text-gray-500 uppercase tracking-wide">
            Recordings
          </p>
          <p className="text-lg font-bold text-white mt-0.5">
            {formatBytes(recBytes)}
          </p>
          <p className="text-xs text-gray-500">
            {stats?.recordings_count ?? 0} files ·{" "}
            {formatDuration(stats?.recordings_total_duration_seconds ?? 0)}
          </p>
        </div>
      </div>

      {/* Usage bars */}
      <div className="space-y-4 mb-5">
        <StorageBar
          label="Disk Usage"
          pct={diskPct}
          detail={`${formatBytes(stats?.disk_used_bytes ?? 0)} / ${formatBytes(stats?.disk_total_bytes ?? 0)}`}
        />
        {capPct !== null && maxGb && (
          <StorageBar
            label="Recording Storage Cap"
            pct={capPct}
            detail={`${formatBytes(recBytes)} / ${maxGb} GB`}
          />
        )}
      </div>

      {/* Per-camera table */}
      <CameraTable cameras={stats?.per_camera ?? []} />

      {/* Settings form */}
      <div className="space-y-4 mb-5">
        <div>
          <label className="block text-xs font-semibold text-gray-400 mb-1.5">
            Max Recording Storage (GB)
          </label>
          <input
            type="number"
            min="0"
            step="1"
            placeholder="Unlimited"
            value={maxGbInput}
            onChange={(e) => setMaxGbInput(e.target.value)}
            className="w-full rounded-lg border border-border bg-elevated px-3.5 py-2.5 text-sm text-white outline-none focus:border-accent placeholder-gray-600"
          />
          <p className="mt-1 text-xs text-gray-600">
            Leave empty for unlimited. Oldest recordings are deleted when the
            cap is exceeded.
          </p>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-400 mb-1.5">
            Warning Threshold (%)
          </label>
          <input
            type="number"
            min="50"
            max="99"
            step="1"
            value={warnPctInput}
            onChange={(e) => setWarnPctInput(Number(e.target.value))}
            className="w-full rounded-lg border border-border bg-elevated px-3.5 py-2.5 text-sm text-white outline-none focus:border-accent"
          />
          <p className="mt-1 text-xs text-gray-600">
            A warning appears when usage exceeds this percentage of the cap (or
            disk if no cap is set). Must be 50–99.
          </p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap items-center gap-3">
        <Button onClick={handleSave} disabled={saving}>
          {saving ? "Saving…" : "Save Changes"}
        </Button>
        <button
          onClick={handleCleanup}
          disabled={cleaning}
          className={cn(
            "inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium transition",
            "text-gray-400 hover:text-white hover:bg-hover",
            "disabled:opacity-50 disabled:cursor-not-allowed"
          )}
        >
          <Trash2 size={14} />
          {cleaning ? "Cleaning…" : "Run Cleanup Now"}
        </button>
        <button
          onClick={fetchAll}
          className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium text-gray-400 hover:text-white hover:bg-hover transition"
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>
    </>
  );
}