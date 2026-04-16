import { Navigate } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { LoginForm } from "./LoginForm";

export default function LoginPage() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  if (isAuthenticated) return <Navigate to="/" replace />;

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400 to-violet-500">
            <ShieldCheck size={32} className="text-white" />
          </div>
          <h1 className="text-2xl font-extrabold">
            Sentinel <span className="text-cyan-400">Vault</span>
          </h1>
          <p className="mt-1 text-sm text-gray-400">
            Sign in to your local security dashboard
          </p>
        </div>
        <div className="card">
          <LoginForm />
        </div>
        <p className="mt-6 text-center text-xs text-gray-500">
          All data is stored locally on this device.
        </p>
      </div>
    </div>
  );
}