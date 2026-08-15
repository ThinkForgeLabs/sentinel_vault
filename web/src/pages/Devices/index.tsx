import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { DeviceCard } from "./DeviceCard";
import { DeviceForm } from "./DeviceForm";
import { devicesApi } from "@/api/devices";
import { useUiStore } from "@/store/uiStore";
import type { Device } from "@/types/device";

export default function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Device | null>(null);
  const [deleting, setDeleting] = useState(false);
  const addToast = useUiStore((s) => s.addToast);

  const fetchDevices = async () => {
    try {
      const data = await devicesApi.list();
      setDevices(data);
    } catch {
      // will be empty in dev
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await devicesApi.delete(deleteTarget.id);
      addToast({ title: `${deleteTarget.name} deleted`, variant: "success" });
      setDeleteTarget(null);
      fetchDevices();
    } catch {
      addToast({ title: "Failed to delete device", variant: "error" });
    } finally {
      setDeleting(false);
    }
  };

  return (
    <>
      <Topbar title="Devices" />
      <div className="flex-1 overflow-y-auto p-4 lg:p-6">
        <PageHeader
          title="Devices"
          description={`${devices.length} sensors and devices configured`}
          action={
            <Button onClick={() => setShowAdd(true)}>
              <Plus size={16} /> Add Device
            </Button>
          }
        />

        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <Spinner size="lg" />
          </div>
        ) : devices.length === 0 ? (
          <div className="card py-16 text-center text-gray-500">
            <p className="mb-4">No devices configured yet.</p>
            <Button onClick={() => setShowAdd(true)}>
              <Plus size={16} /> Add Your First Device
            </Button>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 animate-fade-in">
            {devices.map((device) => (
              <DeviceCard
                key={device.id}
                device={device}
                onDelete={(d) => setDeleteTarget(d)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Add Device Modal */}
      <Modal open={showAdd} onClose={() => setShowAdd(false)} title="Add Device">
        <DeviceForm
          onSuccess={() => {
            setShowAdd(false);
            fetchDevices();
          }}
          onCancel={() => setShowAdd(false)}
        />
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Delete Device"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-400">
            Are you sure you want to delete{" "}
            <span className="font-semibold text-white">
              {deleteTarget?.name}
            </span>
            ? This will remove all associated sensor events.
          </p>
          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={() => setDeleteTarget(null)} disabled={deleting}>
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleDelete}
              loading={deleting}
            >
              Delete Device
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
