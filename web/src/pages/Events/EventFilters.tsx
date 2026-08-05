import { cn } from "@/lib/cn";

// value must match the real Event.event_type values produced by the
// backend (see EVENT_TYPES in lib/constants.ts) — "all" is a UI-only
// sentinel meaning "no event_type filter".
const FILTERS = [
  { label: "All", value: "all" },
  { label: "Motion", value: "motion" },
  { label: "Camera Offline", value: "camera_offline" },
];

interface EventFiltersBarProps {
  active: string;
  onChange: (filter: string) => void;
}

export function EventFiltersBar({ active, onChange }: EventFiltersBarProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {FILTERS.map((f) => (
        <button
          key={f.value}
          onClick={() => onChange(f.value)}
          className={cn(
            "rounded-full border px-3.5 py-1.5 text-xs font-medium transition",
            active === f.value
              ? "border-cyan-400 bg-accent/10 text-cyan-400"
              : "border-border bg-elevated text-gray-400 hover:border-gray-500 hover:text-white"
          )}
        >
          {f.label}
        </button>
      ))}
    </div>
  );
}