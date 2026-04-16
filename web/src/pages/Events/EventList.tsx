import { Badge } from "@/components/ui/Badge";
import { eventTypeLabel } from "@/lib/format";
import { formatTime } from "@/lib/date";
import type { CameraEvent } from "@/types/event";

interface EventListProps {
  events: CameraEvent[];
}

export function EventList({ events }: EventListProps) {
  if (events.length === 0) {
    return (
      <div className="card py-16 text-center text-gray-500">
        No events match this filter.
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {events.map((ev) => (
        <div
          key={ev.id}
          className="card cursor-pointer overflow-hidden p-0 transition hover:border-cyan-800"
        >
          <div className="flex aspect-video items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800 text-2xl text-gray-700">
            ◉
          </div>
          <div className="p-3.5">
            <div className="mb-2 flex items-center gap-2">
              <Badge
                variant={
                  ev.importance === "high"
                    ? "red"
                    : ev.importance === "medium"
                      ? "yellow"
                      : "muted"
                }
              >
                {eventTypeLabel(ev.event_type)}
              </Badge>
              {ev.alerted && <Badge variant="accent">Alerted</Badge>}
            </div>
            <p className="text-sm font-semibold">
              {eventTypeLabel(ev.event_type)}
            </p>
            <p className="mt-0.5 text-xs text-gray-400">
              {formatTime(ev.started_at)} •{" "}
              {ev.clip_duration_seconds ?? 0}s •{" "}
              {Math.round(ev.confidence * 100)}%
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}