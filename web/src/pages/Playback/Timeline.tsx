import { useMemo, useRef, useCallback } from "react";
import type { RecordingSegment } from "./index";
import type { TimelineEventMarker } from "@/api/playback";
import { cn } from "@/lib/cn";

interface Props {
  date: string;
  segments: RecordingSegment[];
  activeSegment: RecordingSegment | null;
  playheadTime: Date | null;
  onClick: (time: Date) => void;
  /** Frigate-style event markers overlaid on the bar (optional). */
  events?: TimelineEventMarker[];
}

const MARKER_COLOR: Record<string, string> = {
  low: "bg-gray-400",
  medium: "bg-cyan-400",
  high: "bg-amber-400",
  critical: "bg-red-500",
};

export function Timeline({
  date,
  segments,
  activeSegment,
  playheadTime,
  onClick,
  events = [],
}: Props) {
  const barRef = useRef<HTMLDivElement>(null);

  const dayStart = useMemo(() => new Date(`${date}T00:00:00`).getTime(), [date]);
  const dayMs = 24 * 60 * 60 * 1000;
  const dayEnd = dayStart + dayMs;

  const bars = useMemo(
    () =>
      segments.map((seg) => {
        const s = Math.max(new Date(seg.start).getTime(), dayStart);
        const e = Math.min(new Date(seg.end).getTime(), dayEnd);
        return {
          id: seg.recording_id,
          left: ((s - dayStart) / dayMs) * 100,
          width: Math.max(((e - s) / dayMs) * 100, 0.15),
          active: activeSegment?.recording_id === seg.recording_id,
        };
      }),
    [segments, dayStart, dayEnd, activeSegment]
  );

  const scrubPct = useMemo(() => {
    if (!playheadTime) return null;
    const t = playheadTime.getTime();
    if (t < dayStart || t > dayEnd) return null;
    return ((t - dayStart) / dayMs) * 100;
  }, [playheadTime, dayStart, dayEnd]);

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      if (!barRef.current) return;
      const rect = barRef.current.getBoundingClientRect();
      const frac = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      onClick(new Date(dayStart + frac * dayMs));
    },
    [dayStart, dayMs, onClick]
  );

  const labels = useMemo(
    () =>
      Array.from({ length: 7 }, (_, i) => {
        const h = i * 4;
        return `${String(h).padStart(2, "0")}:00`;
      }),
    []
  );

  const markers = useMemo(
    () =>
      events
        .map((e) => {
          const t = new Date(e.started_at).getTime();
          if (t < dayStart || t > dayEnd) return null;
          return {
            id: e.event_id,
            left: ((t - dayStart) / dayMs) * 100,
            importance: e.importance,
            type: e.event_type,
          };
        })
        .filter((m): m is NonNullable<typeof m> => m !== null),
    [events, dayStart, dayEnd, dayMs]
  );

  return (
    <div>
      {/* Event marker row (Frigate-style ticks) */}
      {markers.length > 0 && (
        <div className="relative mb-1 h-3">
          {markers.map((m) => (
            <div
              key={m.id}
              title={m.type}
              className={cn(
                "absolute top-0 h-2.5 w-1 -translate-x-1/2 rounded-full",
                MARKER_COLOR[m.importance] ?? "bg-gray-400"
              )}
              style={{ left: `${m.left}%` }}
            />
          ))}
        </div>
      )}

      <div
        ref={barRef}
        onClick={handleClick}
        className="relative h-12 cursor-crosshair overflow-hidden rounded-md bg-gray-800"
      >
        {/* Segment bars */}
        {bars.map((b) => (
          <div
            key={b.id}
            className={`absolute inset-y-0 transition-colors ${
              b.active
                ? "bg-cyan-500/40"
                : "bg-cyan-400/20 hover:bg-cyan-400/30"
            }`}
            style={{ left: `${b.left}%`, width: `${b.width}%` }}
          />
        ))}

        {/* Playhead scrubber */}
        {scrubPct !== null && (
          <div
            className="absolute inset-y-0 z-10 w-0.5 bg-cyan-400"
            style={{ left: `${scrubPct}%` }}
          >
            <div className="absolute -left-1.5 -top-1 h-3.5 w-3.5 rounded-full bg-cyan-400" />
          </div>
        )}
      </div>

      {/* Hour labels */}
      <div className="mt-1 flex justify-between px-0.5">
        {labels.map((l) => (
          <span key={l} className="text-xs text-gray-600">
            {l}
          </span>
        ))}
      </div>
    </div>
  );
}