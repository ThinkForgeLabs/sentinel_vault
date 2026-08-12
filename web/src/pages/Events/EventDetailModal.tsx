// pages/Events/EventDetailModal.tsx

import { useEffect, useRef, useState } from "react";
import { X, Trash2, Download, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { eventTypeLabel } from "@/lib/format";
import { formatTime } from "@/lib/date";
import { downloadFile } from "@/lib/download";
import { useUiStore } from "@/store/uiStore";
import type { CameraEvent } from "@/types/event";

const API = "/api/v1";

interface EventDetailModalProps {
  event: CameraEvent | null;
  onClose: () => void;
  onDelete?: (eventId: string) => void;
}

export function EventDetailModal({ event, onClose, onDelete }: EventDetailModalProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const addToast = useUiStore((s) => s.addToast);

  // Reset confirm state whenever a different event is opened
  useEffect(() => {
    setConfirming(false);
    setDeleting(false);
  }, [event?.id]);

  useEffect(() => {
    if (!event) return;

    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        if (confirming) {
          setConfirming(false);
        } else {
          onClose();
        }
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [event, confirming, onClose]);

  if (!event) return null;

  const duration = event.clip_duration_seconds ?? 0;
  const confidence = Math.round(event.confidence * 100);

  async function handleDelete() {
    if (!confirming) {
      setConfirming(true);
      return;
    }
    setDeleting(true);
    try {
      onDelete?.(event!.id);
    } catch {
      setDeleting(false);
      setConfirming(false);
    }
  }

  async function handleDownload() {
    if (!event) return;
    setDownloading(true);
    try {
      await downloadFile(`/events/${event.id}/clip`, `event_${event.id}.mp4`);
    } catch (err) {
      addToast({
        title: "Download failed",
        description: err instanceof Error ? err.message : "Please try again.",
        variant: "error",
      });
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="w-full max-w-3xl overflow-hidden rounded-xl border border-border bg-surface shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-5 py-3">
          <div className="flex items-center gap-3">
            <Badge
              variant={
                event.importance === "high"
                  ? "red"
                  : event.importance === "medium"
                    ? "yellow"
                    : "muted"
              }
            >
              {event.importance}
            </Badge>
            <h2 className="text-sm font-semibold text-white">
              {eventTypeLabel(event.event_type)}
            </h2>
          </div>

          <div className="flex items-center gap-1">
            {/* Download button */}
            {event.clip_path && (
              <button
                onClick={handleDownload}
                disabled={downloading}
                title="Download clip"
                className="rounded-lg p-1.5 text-gray-400 transition hover:bg-white/10 hover:text-white disabled:opacity-50"
              >
                {downloading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
              </button>
            )}

            {/* Delete button */}
            <button
              onClick={handleDelete}
              disabled={deleting}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                confirming
                  ? "bg-red-600 text-white hover:bg-red-500"
                  : "text-gray-400 hover:bg-white/10 hover:text-red-400"
              } disabled:opacity-50`}
            >
              {deleting ? (
                "Deleting…"
              ) : confirming ? (
                "Confirm delete"
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
            </button>

            {confirming && !deleting && (
              <button
                onClick={() => setConfirming(false)}
                className="rounded-lg px-2 py-1.5 text-xs text-gray-400 transition hover:bg-white/10 hover:text-white"
              >
                Cancel
              </button>
            )}

            {/* Close button */}
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-gray-400 transition hover:bg-white/10 hover:text-white"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Video / Thumbnail */}
        <div className="bg-black">
          {event.clip_path ? (
            <video
              ref={videoRef}
              src={`${API}/events/${event.id}/clip`}
              controls
              autoPlay
              className="aspect-video w-full"
            />
          ) : event.thumbnail_path ? (
            <img
              src={`${API}/events/${event.id}/thumbnail`}
              alt="Event thumbnail"
              className="aspect-video w-full object-cover"
            />
          ) : (
            <div className="flex aspect-video items-center justify-center text-2xl text-gray-700">
              No media available
            </div>
          )}
        </div>

        {/* Details */}
        <div className="border-t border-border px-5 py-4">
          <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
            <div>
              <p className="text-xs text-gray-500">Time</p>
              <p className="text-white">{formatTime(event.started_at)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Duration</p>
              <p className="text-white">{duration}s</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Confidence</p>
              <p className="text-white">{confidence}%</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Camera</p>
              <p className="text-white">{event.camera_id.slice(0, 8)}…</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}