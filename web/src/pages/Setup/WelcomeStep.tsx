import { ShieldCheck, Bell, LayoutGrid, Cpu } from "lucide-react";
import { Button } from "@/components/ui/Button";

const HIGHLIGHTS = [
  { icon: Bell, label: "Realtime alerts on this device and your local network" },
  { icon: LayoutGrid, label: "Multi-camera wall view with synced scrubbing" },
  { icon: Cpu, label: "Motion detection tuned to run on hardware as small as a Raspberry Pi 5" },
];

export function WelcomeStep({ onNext }: { onNext: () => void }) {
  return (
    <div className="space-y-6 text-center">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400 to-violet-500">
        <ShieldCheck size={32} className="text-white" />
      </div>
      <div>
        <h1 className="text-2xl font-extrabold">
          Welcome to Sentinel <span className="text-cyan-400">Vault</span>
        </h1>
        <p className="mt-2 text-sm text-gray-400">
          Let's set up your local security system. This only takes a minute.
        </p>
      </div>

      <div className="space-y-2 text-left">
        {HIGHLIGHTS.map(({ icon: Icon, label }) => (
          <div
            key={label}
            className="flex items-center gap-3 rounded-lg border border-border bg-elevated px-3.5 py-2.5"
          >
            <Icon size={16} className="flex-shrink-0 text-cyan-400" />
            <p className="text-sm text-gray-300">{label}</p>
          </div>
        ))}
      </div>

      <Button onClick={onNext} className="w-full">
        Get Started
      </Button>
      <p className="text-xs text-gray-500">All data is stored locally on this device.</p>
    </div>
  );
}
