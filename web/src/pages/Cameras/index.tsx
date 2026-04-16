import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { CameraCard } from "./CameraCard";
import { CameraForm } from "./CameraForm";
import { camerasApi } from "@/api/cameras";
import { useUiStore } from "@/store/uiStore";
import type { Camera } from "@/types/camera";

export default function CamerasPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Camera | null>(null);
  const [deleting, setDeleting] = useState(false);
  const addToast = useUiStore((s) => s.addToast);

  const fetchCameras = async () => {
    try {
      const data = await camerasApi.list();
      setCameras(data);
    } catch {
      // will be empty in dev
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCameras();
  }, []);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await camerasApi.delete(deleteTarget.id);
      addToast({ title: `${deleteTarget.name} deleted`, variant: "success" });
      setDeleteTarget(null);
      fetchCameras();
    } catch {
      addToast({ title: "Failed to delete camera", variant: "error" });
    } finally {
      setDeleting(false);
    }
  };

  return (
    <>
      <Topbar title="Cameras" />
      <div className="flex-1 overflow-y-auto p-4 lg:p-6">
        <PageHeader
          title="Cameras"
          description={`${cameras.length} cameras configured`}
          action={
            <Button onClick={() => setShowAdd(true)}>
              <Plus size={16} /> Add Camera
            </Button>
          }
        />

        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <Spinner size="lg" />
          </div>
        ) : cameras.length === 0 ? (
          <div className="card py-16 text-center text-gray-500">
            <p className="mb-4">No cameras configured yet.</p>
            <Button onClick={() => setShowAdd(true)}>
              <Plus size={16} /> Add Your First Camera
            </Button>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 animate-fade-in">
            {cameras.map((cam) => (
              <CameraCard
                key={cam.id}
                camera={cam}
                onClick={() => {}}
                onDelete={(camera) => setDeleteTarget(camera)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Add Camera Modal */}
      <Modal open={showAdd} onClose={() => setShowAdd(false)} title="Add Camera">
        <CameraForm
          onSuccess={() => {
            setShowAdd(false);
            fetchCameras();
          }}
          onCancel={() => setShowAdd(false)}
        />
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Delete Camera"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-400">
            Are you sure you want to delete{" "}
            <span className="font-semibold text-white">
              {deleteTarget?.name}
            </span>
            ? This will remove all associated recordings and events.
          </p>
          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={() => setDeleteTarget(null)} disabled={deleting}>
              Cancel
            </Button>
            <Button
              variant="secondary"
              onClick={handleDelete}
              loading={deleting}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              Delete Camera
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}