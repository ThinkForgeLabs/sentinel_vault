import { useMemo, useRef, useCallback } from "react";
import type { RecordingSegment } from "./index";
import type { TimelineEventMarker } from "@/api/playback";
import { cn } from "@/lib/cn";

export interface TimeRange {
  start: Date;
  end: Date;
}

interface Props {
  date: string;
  segments: RecordingSegment[];
  activeSegment: RecordingSegment | null;
  playheadTime: Date | null;
  onClick: (time: Date) => void;
  /** Frigate-style event markers overlaid on the bar (optional). */
  events?: TimelineEventMarker[];
  /** When true, dragging on the bar selects an export range instead of
   * scrubbing/seeking. */
  selecting?: boolean;
  /** Currently selected export range, if any — rendered as a highlight. */
  selection?: TimeRange | null;
  onSelectionChange?: (range: TimeRange | null) => void;
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
  selecting = false,
  selection = null,
  onSelectionChange,
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

  const timeAtEvent = useCallback(
    (e: React.MouseEvent | MouseEvent) => {
      const rect = barRef.current!.getBoundingClientRect();
      const frac = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      return new Date(dayStart + frac * dayMs);
    },
    [dayStart, dayMs]
  );

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      if (!barRef.current || selecting) return;
      onClick(timeAtEvent(e));
    },
    [onClick, selecting, timeAtEvent]
  );

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (!selecting || !barRef.current) return;
      const anchor = timeAtEvent(e);
      onSelectionChange?.({ start: anchor, end: anchor });

      const handleMove = (moveEvt: MouseEvent) => {
        const current = timeAtEvent(moveEvt);
        const [start, end] =
          current < anchor ? [current, anchor] : [anchor, current];
        onSelectionChange?.({ start, end });
      };
      const handleUp = () => {
        window.removeEventListener("mousemove", handleMove);
        window.removeEventListener("mouseup", handleUp);
      };
      window.addEventListener("mousemove", handleMove);
      window.addEventListener("mouseup", handleUp);
    },
    [selecting, timeAtEvent, onSelectionChange]
  );

  const selectionRect = useMemo(() => {
    if (!selection) return null;
    const s = Math.max(selection.start.getTime(), dayStart);
    const e = Math.min(selection.end.getTime(), dayEnd);
    if (e <= s) return null;
    return { left: ((s - dayStart) / dayMs) * 100, width: ((e - s) / dayMs) * 100 };
  }, [selection, dayStart, dayEnd, dayMs]);

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
        onMouseDown={handleMouseDown}
        className={cn(
          "relative h-12 overflow-hidden rounded-md bg-gray-800",
          selecting ? "cursor-col-resize" : "cursor-crosshair"
        )}
      >
        {/* Export range selection highlight */}
        {selectionRect && (
          <div
            className="absolute inset-y-0 z-20 border-x-2 border-amber-400 bg-amber-400/20"
            style={{ left: `${selectionRect.left}%`, width: `${selectionRect.width}%` }}
          />
        )}

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