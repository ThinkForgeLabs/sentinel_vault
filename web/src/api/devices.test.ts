import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { devicesApi } from "./devices";
import { useAuthStore } from "@/store/authStore";
import type { Device, DeviceCreate } from "@/types/device";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const sampleDevice: Device = {
  id: "d1",
  name: "Front Door Sensor",
  device_type: "door_sensor",
  location_label: "Front Door",
  protocol: "zigbee2mqtt",
  mqtt_topic: "zigbee2mqtt/Front Door",
  enabled: true,
  status: "online",
  last_seen_at: null,
  created_at: "2026-01-01T00:00:00Z",
};

describe("devicesApi", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    useAuthStore.getState().logout();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("list() issues a GET to /devices and returns the parsed array", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      jsonResponse([sampleDevice])
    );

    const result = await devicesApi.list();

    expect(result).toEqual([sampleDevice]);
    const [url, init] = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(String(url)).toContain("/devices");
    expect(init?.method).toBeUndefined(); // GET is the fetch default
  });

  it("create() issues a POST with a JSON body of the form data", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      jsonResponse(sampleDevice, 201)
    );

    const payload: DeviceCreate = {
      name: "Front Door Sensor",
      device_type: "door_sensor",
      location_label: "Front Door",
      protocol: "zigbee2mqtt",
      mqtt_topic: "zigbee2mqtt/Front Door",
      enabled: true,
    };

    const result = await devicesApi.create(payload);

    expect(result).toEqual(sampleDevice);
    const [url, init] = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(String(url)).toContain("/devices");
    expect(init?.method).toBe("POST");
    expect(JSON.parse(init?.body as string)).toEqual(payload);
  });

  it("delete() issues a DELETE to /devices/:id", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      new Response(null, { status: 204 })
    );

    await devicesApi.delete("d1");

    const [url, init] = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(String(url)).toContain("/devices/d1");
    expect(init?.method).toBe("DELETE");
  });

  it("attaches the bearer token from the auth store when present", async () => {
    useAuthStore.getState().setTokens("test-access-token", "test-refresh-token");
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      jsonResponse([sampleDevice])
    );

    await devicesApi.list();

    const [, init] = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    const headers = init?.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer test-access-token");
  });

  it("throws the server-provided error detail and logs out on 401", async () => {
    (fetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      jsonResponse({ detail: "Not authenticated" }, 401)
    );
    useAuthStore.getState().setTokens("stale-token", "stale-refresh");

    await expect(devicesApi.list()).rejects.toThrow("Not authenticated");
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
});
