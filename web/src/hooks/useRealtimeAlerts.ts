import { useEffect, useRef } from "react";
import { useAuthStore } from "@/store/authStore";
import { useRealtimeStore } from "@/store/realtimeStore";
import { useUiStore } from "@/store/uiStore";
import { buildWsUrl } from "@/lib/ws";
import type { AlertMessage } from "@/types/realtime";

const IMPORTANCE_VARIANT: Record<
  string,
  "default" | "success" | "error" | "warning"
> = {
  low: "default",
  medium: "default",
  high: "warning",
  critical: "error",
};

/** Short chime via the Web Audio API — no external asset needed. */
function playChime() {
  try {
    const Ctx =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext })
        .webkitAudioContext;
    const ctx = new Ctx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.value = 880;
    gain.gain.value = 0.08;
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.4);
    osc.stop(ctx.currentTime + 0.4);
  } catch {
    // Audio unavailable (autoplay policy, headless env, etc.) — ignore.
  }
}

/** Best-effort local desktop notification (separate from in-app toasts). */
function notifyDesktop(alert: AlertMessage) {
  if (typeof Notification === "undefined") return;
  if (Notification.permission === "granted") {
    new Notification(alert.camera_name ?? alert.device_name ?? "Sentinel Vault", {
      body: `${alert.event_type}${alert.subtype ? ` · ${alert.subtype}` : ""}`,
      tag: alert.event_id ?? undefined,
    });
  } else if (Notification.permission === "default") {
    Notification.requestPermission();
  }
}

/**
 * Owns the realtime alerts WebSocket connection for the whole app.
 * Mounted once from AppShell so alerts keep flowing regardless of which
 * page is active, with automatic reconnect (exponential backoff) whenever
 * the user is authenticated.
 */
export function useRealtimeAlerts() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const addAlert = useRealtimeStore((s) => s.addAlert);
  const setConnected = useRealtimeStore((s) => s.setConnected);
  const addToast = useUiStore((s) => s.addToast);

  const socketRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!isAuthenticated || !accessToken) {
      socketRef.current?.close();
      socketRef.current = null;
      setConnected(false);
      return;
    }

    let cancelled = false;

    const connect = () => {
      if (cancelled) return;
      const ws = new WebSocket(
        buildWsUrl(`/realtime/ws?token=${encodeURIComponent(accessToken)}`)
      );
      socketRef.current = ws;

      ws.onopen = () => {
        retryRef.current = 0;
        setConnected(true);
      };

      ws.onmessage = (evt) => {
        try {
          const data: AlertMessage = JSON.parse(evt.data);
          addAlert(data);
          playChime();
          notifyDesktop(data);
          addToast({
            title: data.camera_name ?? data.device_name ?? "New alert",
            description: `${data.event_type}${data.subtype ? ` · ${data.subtype}` : ""}`,
            variant: IMPORTANCE_VARIANT[data.importance] ?? "default",
          });
        } catch {
          // Malformed frame — ignore rather than crash the socket handler.
        }
      };

      ws.onclose = () => {
        setConnected(false);
        socketRef.current = null;
        if (cancelled) return;
        const delay = Math.min(1000 * 2 ** retryRef.current, 15000);
        retryRef.current += 1;
        timerRef.current = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        ws.close();
      };
    };

    connect();

    return () => {
      cancelled = true;
      if (timerRef.current) clearTimeout(timerRef.current);
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, [isAuthenticated, accessToken, addAlert, setConnected, addToast]);
}
