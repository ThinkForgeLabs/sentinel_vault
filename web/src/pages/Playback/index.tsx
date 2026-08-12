import { useState, useEffect, useCallback } from "react";
import { api } from "@/api/client";
import { playbackApi, type TimelineEventMarker } from "@/api/playback";
import { Topbar } from "@/components/layout/Topbar";
import { PageHeader } from "@/components/layout/PageHeader";
import { PlaybackPlayer } from "./PlaybackPlayer";
import { Timeline } from "./Timeline";

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
            <p className="mb-3 text-sm font-semibold">Timeline</p>
            <Timeline
              date={selectedDate}
              segments={segments}
              activeSegment={activeSegment}
              playheadTime={playheadTime}
              onClick={handleTimelineClick}
              events={timelineEvents}
            />
          </div>
        </div>
      </div>
    </>
  );
}