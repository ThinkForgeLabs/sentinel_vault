import { useRef, useState, useEffect, useCallback } from "react";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Maximize2,
  Loader2,
} from "lucide-react";
import { API_URL } from "@/lib/constants";
import type { RecordingSegment } from "./index";

interface Props {
  segment: RecordingSegment | null;
  seekTo: number | null;
  onSkip: (direction: "prev" | "next") => void;
  onTimeUpdate: (offsetSeconds: number) => void;
  onEnded: () => void;
}

/** Build a direct URL the <video> element can fetch (no custom headers). */
function videoUrl(recordingId: string): string {
  return `${API_URL}/playback/recording/${recordingId}/video`;
}

export function PlaybackPlayer({
  segment,
  seekTo,
  onSkip,
  onTimeUpdate,
  onEnded,
}: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(false);
  const [waiting, setWaiting] = useState(false);
  const [clock, setClock] = useState("00:00:00");
  const lastSegId = useRef<string | null>(null);

  // ── Load new segment ──
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !segment) return;

    const isNew = segment.recording_id !== lastSegId.current;
    lastSegId.current = segment.recording_id;

    if (isNew) {
      video.src = videoUrl(segment.recording_id);
      video.load();

      const onReady = () => {
        if (seekTo !== null && seekTo > 0) {
          video.currentTime = seekTo;
        }
        video.play().catch(() => {});
      };
      video.addEventListener("loadedmetadata", onReady, { once: true });
      return () => video.removeEventListener("loadedmetadata", onReady);
    }
  }, [segment?.recording_id]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Seek within same segment (timeline re-click) ──
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !segment || seekTo === null) return;
    if (segment.recording_id !== lastSegId.current) return;
    if (video.readyState >= 1) {
      video.currentTime = seekTo;
      if (video.paused) video.play().catch(() => {});
    }
  }, [seekTo]); // eslint-disable-line react-hooks/exhaustive-deps

  const togglePlay = useCallback(() => {
    const video = videoRef.current;
    if (!video || !segment) return;
    if (video.paused) {
      video.play().catch(() => {});
    } else {
      video.pause();
    }
  }, [segment]);

  const handleTimeUpdate = useCallback(() => {
    const video = videoRef.current;
    if (!video || !segment) return;
    const offset = video.currentTime;
    onTimeUpdate(offset);
    const wall = new Date(new Date(segment.start).getTime() + offset * 1000);
    setClock(
      `${String(wall.getHours()).padStart(2, "0")}:${String(wall.getMinutes()).padStart(2, "0")}:${String(wall.getSeconds()).padStart(2, "0")}`
    );
  }, [segment, onTimeUpdate]);

  const handleFullscreen = useCallback(() => {
    videoRef.current?.requestFullscreen?.();
  }, []);

  return (
    <div className="relative flex aspect-video items-center justify-center rounded-xl bg-black overflow-hidden">
      {segment ? (
        <>
          <video
            ref={videoRef}
            className="h-full w-full object-contain"
            onTimeUpdate={handleTimeUpdate}
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
            onWaiting={() => setWaiting(true)}
            onPlaying={() => setWaiting(false)}
            onEnded={onEnded}
            onError={(e) => console.error("Video error:", e)}
          />
          {waiting && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/40">
              <Loader2 size={36} className="animate-spin text-cyan-400" />
            </div>
          )}
        </>
      ) : (
        <p className="text-sm text-gray-600">
          Select a camera and click the timeline to begin playback
        </p>
      )}

      {/* Controls */}
      <div className="absolute inset-x-0 bottom-0 flex items-center gap-3 bg-gradient-to-t from-black/80 to-transparent p-4">
        <button onClick={() => onSkip("prev")} className="text-gray-400 hover:text-white transition">
          <SkipBack size={18} />
        </button>
        <button
          onClick={togglePlay}
          className="flex h-10 w-10 items-center justify-center rounded-full bg-white/20 backdrop-blur text-white hover:bg-white/30 transition"
        >
          {playing ? <Pause size={20} /> : <Play size={20} className="ml-0.5" />}
        </button>
        <button onClick={() => onSkip("next")} className="text-gray-400 hover:text-white transition">
          <SkipForward size={18} />
        </button>
        <span className="ml-2 text-xs font-mono text-gray-400">{clock}</span>
        <div className="flex-1" />
        <button onClick={handleFullscreen} className="text-gray-400 hover:text-white transition">
          <Maximize2 size={16} />
        </button>
      </div>
    </div>
  );
}