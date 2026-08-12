import { useState, useEffect, useCallback, useRef } from "react";
import { Play, Pause, LayoutGrid, Rows3 } from "lucide-react";
import { api } from "@/api/client";
import { playbackApi, type PlaybackSegment, type TimelineEventMarker } from "@/api/playback";
import { Topbar } from "@/components/layout/Topbar";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/cn";
import { LiveTile } from "./LiveTile";
import { PlaybackTile } from "./PlaybackTile";
import { Timeline } from "@/pages/Playback/Timeline";
import type { RecordingSegment } from "@/pages/Playback/index";
import type { Camera } from "@/types/camera";

type Mode = "live" | "recorded";

export default function WallPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<Mode>("live");

  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().slice(0, 10)
  );
  const [availability, setAvailability] = useState<Record<string, PlaybackSegment[]>>({});
  const [timelineEvents, setTimelineEvents] = useState<TimelineEventMarker[]>([]);
  const [masterTime, setMasterTime] = useState<Date>(() => new Date());
  const [isPlaying, setIsPlaying] = useState(false);

  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    api
      .get<Camera[]>("/cameras")
      .then((cams) => {
        const list = Array.isArray(cams) ? cams : [];
        setCameras(list);
        setSelectedIds(new Set(list.slice(0, 4).map((c) => c.id)));
      })
      .catch(() => setCameras([]))
      .finally(() => setLoading(false));
  }, []);

  const selectedCameras = cameras.filter((c) => selectedIds.has(c.id));

  const toggleCamera = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // ── Recorded mode: fetch batch availability + timeline markers ──
  useEffect(() => {
    if (mode !== "recorded" || selectedIds.size === 0) return;
    const ids = Array.from(selectedIds);
    const start = `${selectedDate}T00:00:00Z`;
    const end = `${selectedDate}T23:59:59Z`;

    playbackApi
      .batchAvailability(ids, start, end)
      .then((data) => setAvailability(data.cameras))
      .catch(() => setAvailability({}));

    playbackApi
      .timelineEvents(ids, start, end)
      .then((data) => setTimelineEvents(data.events))
      .catch(() => setTimelineEvents([]));

    setMasterTime(new Date(`${selectedDate}T00:00:00`));
    setIsPlaying(false);
  }, [mode, selectedDate, selectedIds]);

  // ── Master clock: advances masterTime while playing, drives every tile ──
  useEffect(() => {
    if (tickRef.current) clearInterval(tickRef.current);
    if (!isPlaying || mode !== "recorded") return;

    tickRef.current = setInterval(() => {
      setMasterTime((t) => new Date(t.getTime() + 250));
    }, 250);

    return () => {
      if (tickRef.current) clearInterval(tickRef.current);
    };
  }, [isPlaying, mode]);

  const handleTimelineClick = useCallback((time: Date) => {
    setMasterTime(time);
  }, []);

  // Merge every selected camera's segments for the shared coverage bar.
  const mergedSegments: RecordingSegment[] = Object.values(availability)
    .flat()
    .filter((s): s is PlaybackSegment & { recording_id: string } => !!s.recording_id)
    .map((s) => ({
      start: s.start,
      end: s.end,
      recording_id: s.recording_id,
      duration_seconds: s.duration_seconds,
    }));

  const gridCols = (n: number) => {
    if (n <= 1) return "grid-cols-1";
    if (n <= 4) return "grid-cols-2";
    if (n <= 9) return "grid-cols-3";
    return "grid-cols-4";
  };

  return (
    <>
      <Topbar title="Wall View" />
      <div className="flex-1 overflow-y-auto p-4 lg:p-6">
        <PageHeader
          title="Wall View"
          description="Watch every camera at once, live or scrubbed together in sync"
          action={
            <div className="flex items-center gap-2 rounded-lg border border-border bg-elevated p-1">
              <button
                onClick={() => setMode("live")}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition",
                  mode === "live" ? "bg-accent/15 text-cyan-400" : "text-gray-400 hover:text-white"
                )}
              >
                <LayoutGrid size={14} /> Live
              </button>
              <button
                onClick={() => setMode("recorded")}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition",
                  mode === "recorded" ? "bg-accent/15 text-cyan-400" : "text-gray-400 hover:text-white"
                )}
              >
                <Rows3 size={14} /> Recorded
              </button>
            </div>
          }
        />

        {/* Camera picker */}
        <div className="mb-4 flex flex-wrap items-center gap-2">
          {cameras.map((c) => (
            <button
              key={c.id}
              onClick={() => toggleCamera(c.id)}
              className={cn(
                "rounded-full border px-3 py-1.5 text-xs font-medium transition",
                selectedIds.has(c.id)
                  ? "border-cyan-400 bg-accent/10 text-cyan-400"
                  : "border-border text-gray-400 hover:text-white"
              )}
            >
              {c.name}
            </button>
          ))}
          {mode === "recorded" && (
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="ml-2 rounded-lg border border-gray-700 bg-gray-800 px-3 py-1.5 text-xs text-gray-200 focus:border-cyan-500 focus:outline-none"
            />
          )}
        </div>

        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <Spinner size="lg" />
          </div>
        ) : selectedCameras.length === 0 ? (
          <div className="card py-16 text-center text-gray-500">
            Select one or more cameras above to build your wall.
          </div>
        ) : (
          <div className="space-y-4 animate-fade-in">
            <div className={cn("grid gap-3", gridCols(selectedCameras.length))}>
              {selectedCameras.map((cam) =>
                mode === "live" ? (
                  <LiveTile key={cam.id} camera={cam} />
                ) : (
                  <PlaybackTile
                    key={cam.id}
                    camera={cam}
                    segments={availability[cam.id] ?? []}
                    masterTime={masterTime}
                    isPlaying={isPlaying}
                  />
                )
              )}
            </div>

            {mode === "recorded" && (
              <div className="card">
                <div className="mb-3 flex items-center justify-between">
                  <p className="text-sm font-semibold">Synced Timeline</p>
                  <Button size="sm" variant="secondary" onClick={() => setIsPlaying((p) => !p)}>
                    {isPlaying ? <Pause size={14} /> : <Play size={14} />}
                    {isPlaying ? "Pause All" : "Play All"}
                  </Button>
                </div>
                <Timeline
                  date={selectedDate}
                  segments={mergedSegments}
                  activeSegment={null}
                  playheadTime={masterTime}
                  onClick={handleTimelineClick}
                  events={timelineEvents}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
