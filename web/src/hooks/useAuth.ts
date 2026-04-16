import { useCallback } from "react";
import { useAuthStore } from "@/store/authStore";
import { authApi } from "@/api/auth";
import { useUiStore } from "@/store/uiStore";
import type { LoginRequest } from "@/types/auth";

export function useAuth() {
  const { setTokens, setUser, logout, isAuthenticated, user } = useAuthStore();
  const addToast = useUiStore((s) => s.addToast);

  const login = useCallback(
    async (data: LoginRequest) => {
      try {
        const tokens = await authApi.login(data);
        setTokens(tokens.access_token, tokens.refresh_token);
        const me = await authApi.me();
        setUser(me);
        addToast({ title: "Welcome back!", variant: "success" });
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Login failed";
        addToast({ title: "Login failed", description: msg, variant: "error" });
        throw err;
      }
    },
    [setTokens, setUser, addToast]
  );

  const fetchUser = useCallback(async () => {
    try {
      const me = await authApi.me();
      setUser(me);
    } catch {
      logout();
    }
  }, [setUser, logout]);

  return { login, logout, fetchUser, isAuthenticated, user };
}