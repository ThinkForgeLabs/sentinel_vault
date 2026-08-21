import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useRealtimeAlerts } from "./useRealtimeAlerts";
import { useAuthStore } from "@/store/authStore";
import { useRealtimeStore } from "@/store/realtimeStore";
import { useUiStore } from "@/store/uiStore";
import type { AlertMessage } from "@/types/realtime";

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  url: string;
  onopen: (() => void) | null = null;
  onmessage: ((evt: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  closed = false;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  close() {
    this.closed = true;
    this.onclose?.();
  }
}

const sensorAlert: AlertMessage = {
  type: "alert",
  event_id: "e1",
  camera_id: null,
  camera_name: null,
  device_id: "dev1",
  device_name: "Front Door Sensor",
  event_type: "door_opened",
  subtype: null,
  importance: "high",
  confidence: 1,
  started_at: "2026-01-01T00:00:00Z",
  thumbnail_url: null,
  clip_url: null,
};

beforeEach(() => {
  MockWebSocket.instances = [];
  vi.stubGlobal("WebSocket", MockWebSocket as unknown as typeof WebSocket);
  useAuthStore.setState({
    accessToken: null,
    refreshToken: null,
    user: null,
    isAuthenticated: false,
  });
  useRealtimeStore.setState({ connected: false, alerts: [], unreadCount: 0, settings: null });
  useUiStore.setState({ toasts: [] });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("useRealtimeAlerts", () => {
  it("does not open a socket when the user is not authenticated", () => {
    renderHook(() => useRealtimeAlerts());
    expect(MockWebSocket.instances).toHaveLength(0);
  });

  it("opens a socket with the access token once authenticated", () => {
    useAuthStore.setState({
      accessToken: "abc123",
      refreshToken: "r1",
      user: null,
      isAuthenticated: true,
    });

    renderHook(() => useRealtimeAlerts());

    expect(MockWebSocket.instances).toHaveLength(1);
    expect(MockWebSocket.instances[0].url).toContain("/realtime/ws?token=abc123");
  });

  it("marks the store connected on open and disconnected on close", async () => {
    useAuthStore.setState({
      accessToken: "abc123",
      refreshToken: "r1",
      user: null,
      isAuthenticated: true,
    });

    renderHook(() => useRealtimeAlerts());
    const socket = MockWebSocket.instances[0];

    act(() => socket.onopen?.());
    expect(useRealtimeStore.getState().connected).toBe(true);

    act(() => socket.onclose?.());
    await waitFor(() => expect(useRealtimeStore.getState().connected).toBe(false));
  });

  it("adds an incoming alert to the realtime store and shows a toast", () => {
    useAuthStore.setState({
      accessToken: "abc123",
      refreshToken: "r1",
      user: null,
      isAuthenticated: true,
    });

    renderHook(() => useRealtimeAlerts());
    const socket = MockWebSocket.instances[0];

    act(() => socket.onmessage?.({ data: JSON.stringify(sensorAlert) }));

    expect(useRealtimeStore.getState().alerts[0]).toEqual(sensorAlert);
    expect(useRealtimeStore.getState().unreadCount).toBe(1);
    expect(useUiStore.getState().toasts[0]).toMatchObject({
      title: "Front Door Sensor",
      description: "door_opened",
    });
  });

  it("ignores a malformed message frame instead of throwing", () => {
    useAuthStore.setState({
      accessToken: "abc123",
      refreshToken: "r1",
      user: null,
      isAuthenticated: true,
    });

    renderHook(() => useRealtimeAlerts());
    const socket = MockWebSocket.instances[0];

    expect(() => socket.onmessage?.({ data: "not json" })).not.toThrow();
    expect(useRealtimeStore.getState().alerts).toHaveLength(0);
  });

  it("closes the socket on unmount", () => {
    useAuthStore.setState({
      accessToken: "abc123",
      refreshToken: "r1",
      user: null,
      isAuthenticated: true,
    });

    const { unmount } = renderHook(() => useRealtimeAlerts());
    const socket = MockWebSocket.instances[0];

    unmount();

    expect(socket.closed).toBe(true);
  });
});
