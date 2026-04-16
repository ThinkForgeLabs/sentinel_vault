import { Zap } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { eventTypeLabel } from "@/lib/format";
import type { CameraEvent } from "@/types/event";

interface RecentEventsProps {
  events: CameraEvent[];
}

export function RecentEvents({ events }: RecentEventsProps) {
  if (events.length === 0) {
    return (
      <div className="card text-center py-12 text-gray-500">
        <Zap size={32} className="mx-auto mb-3 opacity-40" />
        <p>No events today yet</p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {events.map((ev) => (
        <div key={ev.id} className="card cursor-pointer transition hover:border-cyan-800">
          <div className="mb-3 flex items-center justify-between">
            <Badge variant={ev.importance === "high" ? "red" : "muted"}>
              {eventTypeLabel(ev.event_type)}
            </Badge>
            {ev.alerted && <Badge variant="accent">Alerted</Badge>}
          </div>
          <p className="text-sm font-semibold">{eventTypeLabel(ev.event_type)}</p>
          <p className="mt-0.5 text-xs text-gray-400">
            {new Date(ev.started_at).toLocaleTimeString()} •{" "}
            {ev.clip_duration_seconds ?? 0}s clip
          </p>
          <div className="mt-3 text-xs text-gray-500">
            Confidence: {Math.round(ev.confidence * 100)}%
          </div>
        </div>
      ))}
    </div>
  );
}