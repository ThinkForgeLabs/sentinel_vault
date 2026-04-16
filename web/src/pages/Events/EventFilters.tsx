import { cn } from "@/lib/cn";

const FILTERS = ["All", "Person", "Vehicle", "Package", "Pet", "Motion"];

interface EventFiltersBarProps {
  active: string;
  onChange: (filter: string) => void;
}

export function EventFiltersBar({ active, onChange }: EventFiltersBarProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {FILTERS.map((f) => (
        <button
          key={f}
          onClick={() => onChange(f.toLowerCase())}
          className={cn(
            "rounded-full border px-3.5 py-1.5 text-xs font-medium transition",
            active === f.toLowerCase()
              ? "border-cyan-400 bg-accent/10 text-cyan-400"
              : "border-border bg-elevated text-gray-400 hover:border-gray-500 hover:text-white"
          )}
        >
          {f}
        </button>
      ))}
    </div>
  );
}