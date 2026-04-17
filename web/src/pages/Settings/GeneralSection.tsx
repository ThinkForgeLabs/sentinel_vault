import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { cn } from "@/lib/cn";

export function GeneralSection() {
  return (
    <div className="space-y-4">
      <Input label="System Name" defaultValue="Sentinel Vault Home" />
      <div>
        <label className="block text-xs font-semibold text-gray-400 mb-1.5">
          Time Zone
        </label>
        <select className="w-full rounded-lg border border-border bg-elevated px-3.5 py-2.5 text-sm text-white outline-none focus:border-accent">
          <option>America/New_York (UTC-4)</option>
          <option>America/Chicago (UTC-5)</option>
          <option>Europe/London (UTC+1)</option>
        </select>
      </div>
      <div>
        <label className="block text-xs font-semibold text-gray-400 mb-1.5">
          Theme
        </label>
        <div className="flex gap-2">
          {["Dark", "Light", "Auto"].map((t) => (
            <button
              key={t}
              className={cn(
                "rounded-full border px-3.5 py-1.5 text-xs font-medium transition",
                t === "Dark"
                  ? "border-cyan-400 bg-accent/10 text-cyan-400"
                  : "border-border text-gray-400 hover:text-white"
              )}
            >
              {t}
            </button>
          ))}
        </div>
      </div>
      <div className="pt-2">
        <Button>Save Changes</Button>
      </div>
    </div>
  );
}