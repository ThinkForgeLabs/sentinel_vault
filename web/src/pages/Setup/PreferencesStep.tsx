import { Lock, FolderCog } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { cn } from "@/lib/cn";
import type { SetupInitRequest } from "@/types/setup";

interface PreferencesStepProps {
  form: SetupInitRequest;
  update: (patch: Partial<SetupInitRequest>) => void;
  onNext: () => void;
  onBack: () => void;
}

export function PreferencesStep({ form, update, onNext, onBack }: PreferencesStepProps) {
  return (
    <div className="space-y-5">
      <div className="text-center">
        <h2 className="text-lg font-bold">Storage &amp; Security</h2>
        <p className="mt-1 text-sm text-gray-400">
          You can change these later from Settings.
        </p>
      </div>

      <Input
        label="Recordings Storage Path"
        placeholder="./data/recordings"
        value={form.storage_path}
        onChange={(e) => update({ storage_path: e.target.value })}
        hint="Where footage and clips are saved on this device"
      />

      <div className="flex items-center justify-between rounded-lg border border-border bg-elevated px-4 py-3">
        <div className="flex items-start gap-3">
          <Lock size={16} className="mt-0.5 flex-shrink-0 text-cyan-400" />
          <div>
            <p className="text-sm font-medium">Encrypt recordings at rest</p>
            <p className="text-xs text-gray-500">Recommended for most setups</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => update({ encryption_enabled: !form.encryption_enabled })}
          className={cn(
            "h-6 w-11 flex-shrink-0 rounded-full transition-colors",
            form.encryption_enabled ? "bg-cyan-500" : "bg-gray-700"
          )}
        >
          <span
            className={cn(
              "block h-5 w-5 translate-y-0.5 rounded-full bg-white transition-transform",
              form.encryption_enabled ? "translate-x-5" : "translate-x-0.5"
            )}
          />
        </button>
      </div>

      <div className="flex items-start gap-2 rounded-lg bg-elevated/60 px-3.5 py-2.5 text-xs text-gray-500">
        <FolderCog size={13} className="mt-0.5 flex-shrink-0" />
        <p>You can add cameras and fine-tune motion detection right after setup finishes.</p>
      </div>

      <div className="flex items-center justify-between gap-3 pt-2">
        <Button type="button" variant="ghost" onClick={onBack}>
          Back
        </Button>
        <Button type="button" onClick={onNext} className="flex-1">
          Continue
        </Button>
      </div>
    </div>
  );
}
