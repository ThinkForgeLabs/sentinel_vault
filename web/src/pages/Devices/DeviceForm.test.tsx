import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DeviceForm } from "./DeviceForm";
import { devicesApi } from "@/api/devices";
import { useUiStore } from "@/store/uiStore";

vi.mock("@/api/devices", () => ({
  devicesApi: {
    create: vi.fn(),
  },
}));

// jsdom does not implement the browser behavior where clicking a
// type="submit" button dispatches the form's submit event, so tests submit
// the form directly (https://github.com/jsdom/jsdom/issues/1937). Filling
// fields still goes through userEvent to exercise the real onChange handlers.
async function submitForm(container: HTMLElement) {
  const form = container.querySelector("form");
  if (!form) throw new Error("form not found");
  await act(async () => {
    fireEvent.submit(form);
  });
}

describe("DeviceForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useUiStore.setState({ toasts: [] });
  });

  it("shows a validation toast and does not call the API when name and topic are blank", async () => {
    const onSuccess = vi.fn();
    const { container } = render(<DeviceForm onSuccess={onSuccess} onCancel={vi.fn()} />);

    await submitForm(container);

    expect(devicesApi.create).not.toHaveBeenCalled();
    expect(onSuccess).not.toHaveBeenCalled();
    expect(useUiStore.getState().toasts[0]?.title).toBe(
      "Please fill in name and MQTT topic"
    );
  });

  it("submits the filled-in form and calls onSuccess on a successful create", async () => {
    (devicesApi.create as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ id: "d1" });
    const onSuccess = vi.fn();
    const { container } = render(<DeviceForm onSuccess={onSuccess} onCancel={vi.fn()} />);

    await userEvent.type(
      screen.getByPlaceholderText("e.g., Front Door Sensor"),
      "Front Door Sensor"
    );
    await userEvent.type(
      screen.getByPlaceholderText("esphome/front-door or zigbee2mqtt/Front Door"),
      "zigbee2mqtt/Front Door"
    );
    await submitForm(container);

    expect(devicesApi.create).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "Front Door Sensor",
        mqtt_topic: "zigbee2mqtt/Front Door",
        device_type: "presence_sensor",
        protocol: "esphome",
        enabled: true,
      })
    );
    await vi.waitFor(() => expect(onSuccess).toHaveBeenCalled());
    expect(useUiStore.getState().toasts[0]?.title).toBe("Device added");
  });

  it("shows an error toast and keeps the modal open when the API call fails", async () => {
    (devicesApi.create as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error("MQTT topic already in use")
    );
    const onSuccess = vi.fn();
    const { container } = render(<DeviceForm onSuccess={onSuccess} onCancel={vi.fn()} />);

    await userEvent.type(
      screen.getByPlaceholderText("e.g., Front Door Sensor"),
      "Front Door Sensor"
    );
    await userEvent.type(
      screen.getByPlaceholderText("esphome/front-door or zigbee2mqtt/Front Door"),
      "zigbee2mqtt/Front Door"
    );
    await submitForm(container);

    await vi.waitFor(() =>
      expect(useUiStore.getState().toasts[0]).toMatchObject({
        title: "Failed to add device",
        description: "MQTT topic already in use",
        variant: "error",
      })
    );
    expect(onSuccess).not.toHaveBeenCalled();
  });

  it("calls onCancel when the Cancel button is clicked", async () => {
    const onCancel = vi.fn();
    render(<DeviceForm onSuccess={vi.fn()} onCancel={onCancel} />);

    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onCancel).toHaveBeenCalled();
  });
});
