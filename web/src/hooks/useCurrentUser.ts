import { useAuthStore } from "@/store/authStore";

export function useCurrentUser() {
  return useAuthStore((s) => s.user);
}