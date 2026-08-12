import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle2, User as UserIcon, HardDrive, Lock } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { setupApi } from "@/api/setup";
import { useAuthStore } from "@/store/authStore";
import { useUiStore } from "@/store/uiStore";
import type { SetupInitRequest } from "@/types/setup";

interface ReviewStepProps {
  form: SetupInitRequest;
  onBack: () => void;
}

export function ReviewStep({ form, onBack }: ReviewStepProps) {
  const navigate = useNavigate();
  const setTokens = useAuthStore((s) => s.setTokens);
  const setUser = useAuthStore((s) => s.setUser);
  const addToast = useUiStore((s) => s.addToast);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFinish = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await setupApi.init(form);
      setTokens(result.access_token, result.refresh_token);
      setUser(result.user);
      addToast({ title: "Setup complete", description: "Welcome to Sentinel Vault", variant: "success" });
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Setup failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="text-center">
        <h2 className="text-lg font-bold">Review &amp; Finish</h2>
        <p className="mt-1 text-sm text-gray-400">Confirm everything looks right.</p>
      </div>

      <div className="space-y-2">
        <div className="flex items-center gap-3 rounded-lg border border-border bg-elevated px-3.5 py-2.5">
          <UserIcon size={16} className="flex-shrink-0 text-cyan-400" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium">
              {form.admin_display_name || "—"}{" "}
              <span className="text-gray-500">@{form.admin_username || "—"}</span>
            </p>
            <p className="text-xs text-gray-500">Owner account</p>
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-lg border border-border bg-elevated px-3.5 py-2.5">
          <HardDrive size={16} className="flex-shrink-0 text-cyan-400" />
          <div>
            <p className="text-sm font-medium">{form.storage_path || "./data/recordings"}</p>
            <p className="text-xs text-gray-500">Recordings storage path</p>
          </div>
        </div>
        <div className="flex items-center gap-3 rounded-lg border border-border bg-elevated px-3.5 py-2.5">
          <Lock size={16} className="flex-shrink-0 text-cyan-400" />
          <div>
            <p className="text-sm font-medium">
              Encryption {form.encryption_enabled ? "enabled" : "disabled"}
            </p>
            <p className="text-xs text-gray-500">Recordings at rest</p>
          </div>
        </div>
      </div>

      {error && (
        <p className="rounded-lg bg-red-500/10 px-3 py-2 text-xs text-red-400">{error}</p>
      )}

      <div className="flex items-center justify-between gap-3 pt-2">
        <Button type="button" variant="ghost" onClick={onBack} disabled={loading}>
          Back
        </Button>
        <Button type="button" onClick={handleFinish} loading={loading} className="flex-1">
          <CheckCircle2 size={16} /> Complete Setup
        </Button>
      </div>
    </div>
  );
}
