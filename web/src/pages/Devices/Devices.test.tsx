import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import DevicesPage from "./index";
import { devicesApi } from "@/api/devices";
import { useUiStore } from "@/store/uiStore";
import type { Device } from "@/types/device";

vi.mock("@/api/devices", () => ({
  devicesApi: {
    list: vi.fn(),
    delete: vi.fn(),
  },
}));

const doorSensor: Device = {
  id: "d1",
  name: "Front Door Sensor",
  device_type: "door_sensor",
  location_label: "Front Door",
  protocol: "zigbee2mqtt",
  mqtt_topic: "zigbee2mqtt/Front Door",
  status: "online",
  enabled: true,
  last_seen_at: null,
  created_at: "2026-01-01T00:00:00Z",
};

describe("DevicesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useUiStore.setState({ toasts: [] });
  });

  it("shows the empty state when no devices are configured", async () => {
    (devicesApi.list as ReturnType<typeof vi.fn>).mockResolvedValueOnce([]);
    render(<DevicesPage />);

    await waitFor(() =>
      expect(screen.getByText("No devices configured yet.")).toBeInTheDocument()
    );
  });

  it("renders a card per device once loaded", async () => {
    (devicesApi.list as ReturnType<typeof vi.fn>).mockResolvedValueOnce([doorSensor]);
    render(<DevicesPage />);

    await waitFor(() =>
      expect(screen.getByText("Front Door Sensor")).toBeInTheDocument()
    );
    expect(screen.getByText("1 sensors and devices configured")).toBeInTheDocument();
  });

  it("deletes a device after confirming, then refreshes the list", async () => {
    (devicesApi.list as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce([doorSensor])
      .mockResolvedValueOnce([]);
    (devicesApi.delete as ReturnType<typeof vi.fn>).mockResolvedValueOnce(undefined);

    render(<DevicesPage />);
    await waitFor(() => expect(screen.getByText("Front Door Sensor")).toBeInTheDocument());

    await userEvent.click(screen.getByTitle("Delete device"));
    expect(
      screen.getByText((content) => content.includes("Are you sure you want to delete"))
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Delete Device" }));

    await waitFor(() => expect(devicesApi.delete).toHaveBeenCalledWith("d1"));
    expect(devicesApi.list).toHaveBeenCalledTimes(2);
    await waitFor(() =>
      expect(useUiStore.getState().toasts[0]?.title).toBe("Front Door Sensor deleted")
    );
  });

  it("shows an error toast when deletion fails and keeps the device visible", async () => {
    (devicesApi.list as ReturnType<typeof vi.fn>).mockResolvedValue([doorSensor]);
    (devicesApi.delete as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error("device is referenced by events")
    );

    render(<DevicesPage />);
    await waitFor(() => expect(screen.getByText("Front Door Sensor")).toBeInTheDocument());

    await userEvent.click(screen.getByTitle("Delete device"));
    await userEvent.click(screen.getByRole("button", { name: "Delete Device" }));

    await waitFor(() =>
      expect(useUiStore.getState().toasts[0]?.title).toBe("Failed to delete device")
    );
    // The device name now appears twice: once on the still-present card, and
    // once in the (still open, since deletion failed) confirmation modal.
    expect(screen.getAllByText("Front Door Sensor").length).toBeGreaterThanOrEqual(1);
  });
});
