import { useState } from "react";
import { cn } from "@/lib/cn";
import type { SetupInitRequest } from "@/types/setup";
import { WelcomeStep } from "./WelcomeStep";
import { AccountStep } from "./AccountStep";
import { PreferencesStep } from "./PreferencesStep";
import { ReviewStep } from "./ReviewStep";

const STEPS = ["Welcome", "Account", "Preferences", "Review"];

export default function SetupPage() {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<SetupInitRequest>({
    storage_path: "./data/recordings",
    admin_username: "",
    admin_display_name: "",
    admin_password: "",
    encryption_enabled: true,
  });

  const update = (patch: Partial<SetupInitRequest>) =>
    setForm((prev) => ({ ...prev, ...patch }));

  const next = () => setStep((s) => Math.min(s + 1, STEPS.length - 1));
  const back = () => setStep((s) => Math.max(s - 1, 0));

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        {/* ── Step progress ── */}
        {step > 0 && (
          <div className="mb-6 flex items-center gap-2">
            {STEPS.slice(1).map((label, i) => (
              <div key={label} className="flex flex-1 items-center gap-2">
                <div
                  className={cn(
                    "h-1.5 flex-1 rounded-full transition-colors",
                    i + 1 <= step ? "bg-cyan-400" : "bg-elevated"
                  )}
                />
              </div>
            ))}
          </div>
        )}

        <div className="card animate-fade-in">
          {step === 0 && <WelcomeStep onNext={next} />}
          {step === 1 && (
            <AccountStep form={form} update={update} onNext={next} onBack={back} />
          )}
          {step === 2 && (
            <PreferencesStep form={form} update={update} onNext={next} onBack={back} />
          )}
          {step === 3 && <ReviewStep form={form} onBack={back} />}
        </div>
      </div>
    </div>
  );
}
