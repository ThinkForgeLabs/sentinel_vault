import { VideoOff, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import type { Camera } from "@/types/camera";

interface CameraCardProps {
  camera: Camera;
  onClick: (camera: Camera) => void;
  onDelete: (camera: Camera) => void;
}

export function CameraCard({ camera, onClick, onDelete }: CameraCardProps) {
  const isOnline = camera.status === "online";

  return (
    <div
      onClick={() => onClick(camera)}
      className="group card cursor-pointer overflow-hidden p-0 transition hover:border-cyan-800"
    >
      <div className="relative flex aspect-video items-center justify-center bg-black/40">
        {isOnline ? (
          <img
            src={`/api/v1/cameras/${camera.id}/stream`}
            alt={camera.name}
            className="h-full w-full object-cover"
          />
        ) : (
          <VideoOff size={32} className="text-red-500/60" />
        )}
        <div className="absolute left-2.5 top-2.5 flex items-center gap-1.5 rounded-md bg-black/60 px-2 py-1 text-xs font-semibold backdrop-blur-sm">
          <span
            className={`h-2 w-2 rounded-full ${isOnline ? "bg-emerald-400 shadow-emerald-400/50 shadow-sm" : "bg-red-500"}`}
          />
          {camera.name}
        </div>
        {camera.record_enabled && isOnline && (
          <div className="absolute right-2.5 top-2.5 flex items-center gap-1 rounded-md bg-red-500/90 px-2 py-0.5 text-xs font-bold text-white">
            <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-white" />
            REC
          </div>
        )}

        {/* Delete button — visible on hover */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(camera);
          }}
          className="absolute bottom-2.5 right-2.5 rounded-lg bg-black/60 p-2 text-gray-400 opacity-0 transition hover:bg-red-500/80 hover:text-white group-hover:opacity-100"
          title="Delete camera"
        >
          <Trash2 size={14} />
        </button>
      </div>

      <div className="flex items-center justify-between px-3.5 py-3">
        <div>
          <p className="text-sm font-semibold">{camera.name}</p>
          <p className="text-xs text-gray-500">
            {camera.location_label || "No location"}
          </p>
        </div>
        <div className="flex gap-1.5">
          <Badge variant="muted">{camera.retention_days}d</Badge>
        </div>
      </div>
    </div>
  );
}