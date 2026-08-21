import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DeviceCard } from "./DeviceCard";
import type { Device } from "@/types/device";

const baseDevice: Device = {
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

describe("DeviceCard", () => {
  it("renders name, location, type label, and protocol", () => {
    render(<DeviceCard device={baseDevice} onDelete={vi.fn()} />);

    expect(screen.getByText("Front Door Sensor")).toBeInTheDocument();
    expect(screen.getByText("Front Door")).toBeInTheDocument();
    expect(screen.getByText("Door Sensor")).toBeInTheDocument();
    expect(screen.getByText("zigbee2mqtt")).toBeInTheDocument();
  });

  it("shows an Online badge and no Disabled badge for an enabled, online device", () => {
    render(<DeviceCard device={baseDevice} onDelete={vi.fn()} />);

    expect(screen.getByText("Online")).toBeInTheDocument();
    expect(screen.queryByText("Offline")).not.toBeInTheDocument();
    expect(screen.queryByText("Disabled")).not.toBeInTheDocument();
  });

  it("shows an Offline badge for an offline device", () => {
    render(<DeviceCard device={{ ...baseDevice, status: "offline" }} onDelete={vi.fn()} />);

    expect(screen.getByText("Offline")).toBeInTheDocument();
    expect(screen.queryByText("Online")).not.toBeInTheDocument();
  });

  it("shows a Disabled badge when the device is disabled", () => {
    render(<DeviceCard device={{ ...baseDevice, enabled: false }} onDelete={vi.fn()} />);

    expect(screen.getByText("Disabled")).toBeInTheDocument();
  });

  it("falls back to 'No location' when location_label is empty", () => {
    render(<DeviceCard device={{ ...baseDevice, location_label: "" }} onDelete={vi.fn()} />);

    expect(screen.getByText("No location")).toBeInTheDocument();
  });

  it("calls onDelete with the device when the delete button is clicked", async () => {
    const onDelete = vi.fn();
    render(<DeviceCard device={baseDevice} onDelete={onDelete} />);

    await userEvent.click(screen.getByTitle("Delete device"));

    expect(onDelete).toHaveBeenCalledWith(baseDevice);
  });
});
