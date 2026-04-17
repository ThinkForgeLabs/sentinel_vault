// pages/Events/EventCard.tsx

import { Badge } from "@/components/ui/Badge";
import { eventTypeLabel } from "@/lib/format";
import { formatTime } from "@/lib/date";
import { Play } from "lucide-react";
import type { CameraEvent } from "@/types/event";

const API = "/api/v1";

interface EventCardProps {
  event: CameraEvent;
  onClick?: (event: CameraEvent) => void;
}

export function EventCard({ event, onClick }: EventCardProps) {
  const duration = event.clip_duration_seconds ?? 0;
  const confidence = Math.round(event.confidence * 100);
  const hasClip = !!event.clip_path;

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onClick?.(event)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") onClick?.(event);
      }}
      className="card cursor-pointer overflow-hidden p-0 transition hover:border-cyan-800 focus:outline-none focus:ring-1 focus:ring-cyan-600"
    >
      {/* ── Thumbnail ── */}
      <div className="relative">
        {event.thumbnail_path ? (
          <img
            src={`${API}/events/${event.id}/thumbnail`}
            alt={eventTypeLabel(event.event_type)}
            className="aspect-video w-full object-cover bg-gray-900"
            loading="lazy"
          />
        ) : (
          <div className="flex aspect-video items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800 text-2xl text-gray-700">
            ◉
          </div>
        )}

        {/* Play overlay */}
        {hasClip && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 transition hover:opacity-100">
            <Play className="h-10 w-10 text-white drop-shadow-lg" fill="white" />
          </div>
        )}

        {/* Duration badge */}
        {duration > 0 && (
          <span className="absolute bottom-2 right-2 rounded bg-black/70 px-1.5 py-0.5 text-xs font-medium text-white">
            {duration}s
          </span>
        )}
      </div>

      {/* ── Details ── */}
      <div className="p-3.5">
        <div className="mb-2 flex items-center gap-2">
          <Badge
            variant={
              event.importance === "high"
                ? "red"
                : event.importance === "medium"
                  ? "yellow"
                  : "muted"
            }
          >
            {eventTypeLabel(event.event_type)}
          </Badge>
          {event.alerted && <Badge variant="accent">Alerted</Badge>}
        </div>

        <p className="text-sm font-semibold text-white">
          {eventTypeLabel(event.event_type)}
        </p>

        <p className="mt-0.5 text-xs text-gray-400">
          {formatTime(event.started_at)} • {duration}s • {confidence}%
        </p>
      </div>
    </div>
  );
}