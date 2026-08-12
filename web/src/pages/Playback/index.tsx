import { useState, useEffect, useCallback } from "react";
import { Scissors, Download, X, Loader2 } from "lucide-react";
import { api } from "@/api/client";
import { playbackApi, type TimelineEventMarker } from "@/api/playback";
import { Topbar } from "@/components/layout/Topbar";
import { PageHeader } from "@/components/layout/PageHeader";
import { downloadFile } from "@/lib/download";
import { useUiStore } from "@/store/uiStore";
import { PlaybackPlayer } from "./PlaybackPlayer";
import { Timeline, type TimeRange } from "./Timeline";

export interface RecordingSegment {
  start: string;
  end: string;
  recording_id: string;
  duration_seconds: number;
}

interface AvailabilityResponse {
  camera_id: string;
  segments: RecordingSegment[];
}

interface Camera {
  id: string;
  name: string;
}

export default function PlaybackPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [selectedCamera, setSelectedCamera] = useState("");
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().slice(0, 10)
  );
  const [segments, setSegments] = useState<RecordingSegment[]>([]);
  const [activeSegment, setActiveSegment] = useState<RecordingSegment | null>(
    null
  );
  const [seekTo, setSeekTo] = useState<number | null>(null);
  const [playheadTime, setPlayheadTime] = useState<Date | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEventMarker[]>([]);
  const [exportMode, setExportMode] = useState(false);
  const [exportRange, setExportRange] = useState<TimeRange | null>(null);
  const [exporting, setExporting] = useState(false);
  const [downloadingSegment, setDownloadingSegment] = useState(false);
  const addToast = useUiStore((s) => s.addToast);

  // Fetch cameras on mount
  useEffect(() => {
    api
      .get<Camera[]>("/cameras")
      .then((cams) => {
        const list = Array.isArray(cams) ? cams : [];
        setCameras(list);
        if (list.length > 0) setSelectedCamera(list[0].id);
      })
      .catch((err) => {
        setError(err.message ?? "Failed to load cameras");
        setCameras([]);
      });
  }, []);

  // Fetch availability when camera or date changes
  useEffect(() => {
    if (!selectedCamera || !selectedDate) return;

    setLoading(true);
    setError(null);

    api
      .get<AvailabilityResponse>("/playback/availability", {
        camera_id: selectedCamera,
        start: `${selectedDate}T00:00:00Z`,
        end: `${selectedDate}T23:59:59Z`,
      })
      .then((data) => {
        const segs = Array.isArray(data?.segments) ? data.segments : [];
        setSegments(segs);

        // ── Auto-select the first segment so play works immediately ──
        if (segs.length > 0) {
          setActiveSegment(segs[0]);
          setSeekTo(0);
        } else {
          setActiveSegment(null);
        }
        setPlayheadTime(null);
      })
      .catch((err) => {
        setError(err.message ?? "Failed to load availability");
        setSegments([]);
        setActiveSegment(null);
      })
      .finally(() => setLoading(false));

    playbackApi
      .timelineEvents(
        [selectedCamera],
        `${selectedDate}T00:00:00Z`,
        `${selectedDate}T23:59:59Z`
      )
      .then((data) => setTimelineEvents(data.events))
      .catch(() => setTimelineEvents([]));
  }, [selectedCamera, selectedDate]);

  const handleTimelineClick = useCallback(
    (time: Date) => {
      const seg = segments.find(
        (s) => new Date(s.start) <= time && new Date(s.end) >= time
      );
      if (seg) {
        const offset = (time.getTime() - new Date(seg.start).getTime()) / 1000;
        setActiveSegment(seg);
        setSeekTo(offset);
      }
    },
    [segments]
  );

  const handleSkip = useCallback(
    (direction: "prev" | "next") => {
      if (!activeSegment || segments.length === 0) return;
      const idx = segments.findIndex(
        (s) => s.recording_id === activeSegment.recording_id
      );
      const next =
        direction === "prev" ? segments[idx - 1] : segments[idx + 1];
      if (next) {
        setActiveSegment(next);
        setSeekTo(0);
      }
    },
    [activeSegment, segments]
  );

  const handleTimeUpdate = useCallback(
    (offsetSeconds: number) => {
      if (!activeSegment) return;
      setPlayheadTime(
        new Date(new Date(activeSegment.start).getTime() + offsetSeconds * 1000)
      );
    },
    [activeSegment]
  );

  const handleSegmentEnd = useCallback(() => {
    handleSkip("next");
  }, [handleSkip]);

  const toggleExportMode = useCallback(() => {
    setExportMode((v) => !v);
    setExportRange(null);
  }, []);

  const cameraName = cameras.find((c) => c.id === selectedCamera)?.name ?? "camera";

  const exportDurationLabel = (() => {
    if (!exportRange) return null;
    const seconds = Math.max(
      0,
      Math.round((exportRange.end.getTime() - exportRange.start.getTime()) / 1000)
    );
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}m ${s}s`;
  })();

  const handleExportDownload = useCallback(async () => {
    if (!exportRange || !selectedCamera) return;
    setExporting(true);
    try {
      const path = playbackApi.exportPath(
        selectedCamera,
        exportRange.start.toISOString(),
        exportRange.end.toISOString()
      );
      await downloadFile(path, `${cameraName}_export.mp4`);
      setExportMode(false);
      setExportRange(null);
    } catch (err) {
      addToast({
        title: "Export failed",
        description: err instanceof Error ? err.message : "Please try again.",
        variant: "error",
      });
    } finally {
      setExporting(false);
    }
  }, [exportRange, selectedCamera, cameraName, addToast]);

  const handleDownloadSegment = useCallback(async () => {
    if (!activeSegment) return;
    setDownloadingSegment(true);
    try {
      await downloadFile(
        `/recordings/${activeSegment.recording_id}/download`,
        `recording_${activeSegment.recording_id}.avi`
      );
    } catch (err) {
      addToast({
        title: "Download failed",
        description: err instanceof Error ? err.message : "Please try again.",
        variant: "error",
      });
    } finally {
      setDownloadingSegment(false);
    }
  }, [activeSegment, addToast]);

  return (
    <>
      <Topbar title="Playback" />
      <div className="flex-1 overflow-y-auto p-4 lg:p-6">
        <PageHeader
          title="Playback"
          description="Scrub through recordings and review events"
        />

        {error && (
          <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-400">
            {error}
          </div>
        )}

        <div className="mb-4 flex flex-wrap items-center gap-3">
          <select
            value={selectedCamera}
            onChange={(e) => setSelectedCamera(e.target.value)}
            className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 focus:border-cyan-500 focus:outline-none"
          >
            <option value="">Select camera</option>
            {cameras.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>

          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 focus:border-cyan-500 focus:outline-none"
          />

          <span className="text-xs text-gray-500">
            {loading
              ? "Loading…"
              : `${segments.length} segment${segments.length !== 1 ? "s" : ""} found`}
          </span>

          <div className="flex-1" />

          <button
            onClick={handleDownloadSegment}
            disabled={!activeSegment || downloadingSegment}
            className="flex items-center gap-1.5 rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-xs font-medium text-gray-300 transition hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {downloadingSegment ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Download className="h-3.5 w-3.5" />
            )}
            Download segment
          </button>

          <button
            onClick={toggleExportMode}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition ${
              exportMode
                ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                : "border border-gray-700 bg-gray-800 text-gray-300 hover:bg-gray-700"
            }`}
          >
            {exportMode ? <X className="h-3.5 w-3.5" /> : <Scissors className="h-3.5 w-3.5" />}
            {exportMode ? "Cancel export" : "Select range to export"}
          </button>
        </div>

        <div className="space-y-4 animate-fade-in">
          <PlaybackPlayer
            segment={activeSegment}
            seekTo={seekTo}
            onSkip={handleSkip}
            onTimeUpdate={handleTimeUpdate}
            onEnded={handleSegmentEnd}
          />

          <div className="card">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-sm font-semibold">
                {exportMode ? "Drag to select a range to export" : "Timeline"}
              </p>
              {exportMode && exportRange && (
                <div className="flex items-center gap-3">
                  <span className="text-xs text-amber-300">
                    {exportRange.start.toLocaleTimeString()} – {exportRange.end.toLocaleTimeString()}
                    {exportDurationLabel && ` (${exportDurationLabel})`}
                  </span>
                  <button
                    onClick={handleExportDownload}
                    disabled={exporting}
                    className="flex items-center gap-1.5 rounded-lg bg-amber-500 px-3 py-1.5 text-xs font-semibold text-black transition hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {exporting ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Download className="h-3.5 w-3.5" />
                    )}
                    {exporting ? "Exporting…" : "Export & download"}
                  </button>
                </div>
              )}
            </div>
            <Timeline
              date={selectedDate}
              segments={segments}
              activeSegment={activeSegment}
              playheadTime={playheadTime}
              onClick={handleTimelineClick}
              events={timelineEvents}
              selecting={exportMode}
              selection={exportRange}
              onSelectionChange={setExportRange}
            />
          </div>
        </div>
      </div>
    </>
  );
}