import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { Spinner } from "@/components/ui/Spinner";
import { setupApi } from "@/api/setup";
import type { SetupState } from "@/types/setup";

/**
 * Gates every route behind a first-run setup check. Until an owner account
 * exists, every path (including /login) redirects to /setup; once setup is
 * complete, /setup itself redirects away. Re-checked on every top-level
 * navigation so completing the wizard immediately unlocks the rest of the
 * app without a hard reload.
 */
export function RootGate() {
  const location = useLocation();
  const [state, setState] = useState<SetupState | null>(null);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setupApi
      .state()
      .then((s) => {
        if (!cancelled) setState(s);
      })
      .catch(() => {
        // If the setup-state check itself fails (e.g. API unreachable),
        // don't trap the user on a broken wizard -- fall through to login.
        if (!cancelled) setState({ complete: true, step: "complete" });
      })
      .finally(() => {
        if (!cancelled) setChecked(true);
      });
    return () => {
      cancelled = true;
    };
  }, [location.pathname]);

  if (!checked || !state) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-background">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400 to-violet-500">
          <ShieldCheck size={28} className="text-white" />
        </div>
        <Spinner size="lg" />
      </div>
    );
  }

  if (!state.complete && location.pathname !== "/setup") {
    return <Navigate to="/setup" replace />;
  }

  if (state.complete && location.pathname === "/setup") {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
