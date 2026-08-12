import { useRef, useEffect } from "react";
import { VideoOff } from "lucide-react";
import { API_URL } from "@/lib/constants";
import type { Camera } from "@/types/camera";
import type { PlaybackSegment } from "@/api/playback";

interface Props {
  camera: Camera;
  segments: PlaybackSegment[];
  masterTime: Date;
  isPlaying: boolean;
}

const DRIFT_TOLERANCE_S = 0.75;

function videoUrl(recordingId: string): string {
  return `${API_URL}/playback/recording/${recordingId}/video`;
}

export function PlaybackTile({ camera, segments, masterTime, isPlaying }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const loadedRecordingId = useRef<string | null>(null);

  const activeSegment = segments.find(
    (s) =>
      s.recording_id &&
      new Date(s.start).getTime() <= masterTime.getTime() &&
      new Date(s.end).getTime() >= masterTime.getTime()
  );

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    if (!activeSegment || !activeSegment.recording_id) {
      video.pause();
      return;
    }

    const desiredOffset =
      (masterTime.getTime() - new Date(activeSegment.start).getTime()) / 1000;

    const isNewRecording = activeSegment.recording_id !== loadedRecordingId.current;

    if (isNewRecording) {
      loadedRecordingId.current = activeSegment.recording_id;
      video.src = videoUrl(activeSegment.recording_id);
      video.load();
      const onReady = () => {
        video.currentTime = Math.max(0, desiredOffset);
        if (isPlaying) video.play().catch(() => {});
      };
      video.addEventListener("loadedmetadata", onReady, { once: true });
      return () => video.removeEventListener("loadedmetadata", onReady);
    }

    // Same recording still active — correct drift without a full reload.
    if (video.readyState >= 1) {
      const drift = Math.abs(video.currentTime - desiredOffset);
      if (drift > DRIFT_TOLERANCE_S) {
        video.currentTime = Math.max(0, desiredOffset);
      }
      if (isPlaying && video.paused) video.play().catch(() => {});
      if (!isPlaying && !video.paused) video.pause();
    }
  }, [activeSegment, masterTime, isPlaying]);

  return (
    <div className="relative flex aspect-video items-center justify-center overflow-hidden rounded-xl border border-border bg-black/60">
      <video
        ref={videoRef}
        className={`h-full w-full object-contain ${activeSegment ? "" : "hidden"}`}
        muted
      />
      {!activeSegment && (
        <div className="flex flex-col items-center gap-1.5 text-gray-600">
          <VideoOff size={24} />
          <span className="text-xs">No recording</span>
        </div>
      )}
      <div className="absolute left-2.5 top-2.5 flex items-center gap-1.5 rounded-md bg-black/60 px-2 py-1 text-xs font-semibold backdrop-blur-sm">
        <span
          className={`h-2 w-2 rounded-full ${activeSegment ? "bg-cyan-400" : "bg-gray-600"}`}
        />
        {camera.name}
      </div>
    </div>
  );
}
