import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import type { SetupInitRequest } from "@/types/setup";

interface AccountStepProps {
  form: SetupInitRequest;
  update: (patch: Partial<SetupInitRequest>) => void;
  onNext: () => void;
  onBack: () => void;
}

export function AccountStep({ form, update, onNext, onBack }: AccountStepProps) {
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.admin_display_name.trim() || !form.admin_username.trim()) {
      setError("Please fill in every field.");
      return;
    }
    if (form.admin_password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (form.admin_password !== confirmPassword) {
      setError("Passwords don't match.");
      return;
    }
    setError("");
    onNext();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="text-center">
        <h2 className="text-lg font-bold">Create Your Owner Account</h2>
        <p className="mt-1 text-sm text-gray-400">
          This account has full access, including managing other accounts.
        </p>
      </div>

      <Input
        label="Display Name"
        placeholder="e.g., Alex"
        value={form.admin_display_name}
        onChange={(e) => update({ admin_display_name: e.target.value })}
        autoFocus
        required
      />
      <Input
        label="Username"
        placeholder="admin"
        value={form.admin_username}
        onChange={(e) => update({ admin_username: e.target.value })}
        required
      />
      <Input
        label="Password"
        type="password"
        placeholder="••••••••"
        value={form.admin_password}
        onChange={(e) => update({ admin_password: e.target.value })}
        hint="At least 8 characters"
        required
      />
      <Input
        label="Confirm Password"
        type="password"
        placeholder="••••••••"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        required
      />

      {error && (
        <p className="rounded-lg bg-red-500/10 px-3 py-2 text-xs text-red-400">{error}</p>
      )}

      <div className="flex items-center justify-between gap-3 pt-2">
        <Button type="button" variant="ghost" onClick={onBack}>
          Back
        </Button>
        <Button type="submit" className="flex-1">
          Continue
        </Button>
      </div>
    </form>
  );
}
