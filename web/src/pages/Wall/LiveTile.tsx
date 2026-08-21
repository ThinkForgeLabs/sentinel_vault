import { VideoOff } from "lucide-react";
import { API_URL } from "@/lib/constants";
import type { Camera } from "@/types/camera";

interface Props {
  camera: Camera;
}

export function LiveTile({ camera }: Props) {
  const isOnline = camera.status === "online";

  return (
    <div className="relative flex aspect-video items-center justify-center overflow-hidden rounded-xl border border-border bg-black/40">
      {isOnline ? (
        <img
          src={`${API_URL}/cameras/${camera.id}/stream`}
          alt={camera.name}
          className="h-full w-full object-cover"
        />
      ) : (
        <VideoOff size={28} className="text-red-500/60" />
      )}
      <div className="absolute left-2.5 top-2.5 flex items-center gap-1.5 rounded-md bg-black/60 px-2 py-1 text-xs font-semibold backdrop-blur-sm">
        <span
          className={`h-2 w-2 rounded-full ${isOnline ? "bg-emerald-400 shadow-emerald-400/50 shadow-sm" : "bg-red-500"}`}
        />
        {camera.name}
      </div>
    </div>
  );
}
