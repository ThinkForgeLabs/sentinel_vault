import { useEffect, useState } from "react";
import { Plus, Trash2, ShieldCheck, Eye } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { usersApi, type UserCreate } from "@/api/users";
import { useUiStore } from "@/store/uiStore";
import { useAuth } from "@/hooks/useAuth";
import type { User } from "@/types/auth";

function CreateUserModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}) {
  const addToast = useUiStore((s) => s.addToast);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState<UserCreate>({
    username: "",
    display_name: "",
    password: "",
    role: "viewer",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await usersApi.create(form);
      addToast({ title: "Account created", variant: "success" });
      setForm({ username: "", display_name: "", password: "", role: "viewer" });
      onCreated();
      onClose();
    } catch (err) {
      addToast({
        title: "Failed to create account",
        description: err instanceof Error ? err.message : undefined,
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Add Account">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Display Name"
          value={form.display_name}
          onChange={(e) => setForm((f) => ({ ...f, display_name: e.target.value }))}
          required
        />
        <Input
          label="Username"
          value={form.username}
          onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
          required
        />
        <Input
          label="Password"
          type="password"
          value={form.password}
          onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
          hint="At least 8 characters"
          required
        />
        <div>
          <label className="block text-xs font-semibold text-gray-400 mb-1.5">Role</label>
          <div className="flex gap-2">
            {(["viewer", "owner"] as const).map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setForm((f) => ({ ...f, role: r }))}
                className={`flex-1 rounded-lg border px-3 py-2 text-sm font-medium capitalize transition ${
                  form.role === r
                    ? "border-cyan-400 bg-accent/10 text-cyan-400"
                    : "border-border text-gray-400 hover:text-white"
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={loading}>
            Create Account
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function TeamAccounts() {
  const addToast = useUiStore((s) => s.addToast);
  const currentUser = useAuth().user;
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<User | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fetchUsers = async () => {
    try {
      const data = await usersApi.list();
      setUsers(data);
    } catch {
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const toggleActive = async (u: User) => {
    try {
      await usersApi.update(u.id, { is_active: !u.is_active });
      fetchUsers();
    } catch (err) {
      addToast({
        title: "Failed to update account",
        description: err instanceof Error ? err.message : undefined,
        variant: "error",
      });
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await usersApi.delete(deleteTarget.id);
      addToast({ title: `${deleteTarget.display_name} removed`, variant: "success" });
      setDeleteTarget(null);
      fetchUsers();
    } catch (err) {
      addToast({
        title: "Failed to delete account",
        description: err instanceof Error ? err.message : undefined,
        variant: "error",
      });
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-24 items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-gray-300">Team Accounts</p>
        <Button size="sm" onClick={() => setShowAdd(true)}>
          <Plus size={14} /> Add Account
        </Button>
      </div>

      <div className="space-y-2">
        {users.map((u) => (
          <div
            key={u.id}
            className="flex items-center gap-3 rounded-lg border border-border bg-elevated px-3.5 py-2.5"
          >
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-cyan-400 text-xs font-bold text-white">
              {u.display_name.slice(0, 2).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold">{u.display_name}</p>
              <p className="truncate text-xs text-gray-500">@{u.username}</p>
            </div>
            <Badge variant={u.role === "owner" ? "purple" : "muted"}>
              {u.role === "owner" ? <ShieldCheck size={11} /> : <Eye size={11} />}
              {u.role}
            </Badge>
            <button
              onClick={() => toggleActive(u)}
              className={`rounded-full px-2.5 py-0.5 text-xs font-semibold transition ${
                u.is_active
                  ? "bg-emerald-500/12 text-emerald-400 hover:bg-emerald-500/20"
                  : "bg-gray-700/50 text-gray-400 hover:bg-hover"
              }`}
            >
              {u.is_active ? "Active" : "Disabled"}
            </button>
            <button
              onClick={() => setDeleteTarget(u)}
              disabled={u.id === currentUser?.id}
              title={u.id === currentUser?.id ? "You can't remove your own account here" : "Remove account"}
              className="rounded-lg p-1.5 text-gray-500 transition hover:bg-red-500/10 hover:text-red-400 disabled:opacity-30 disabled:pointer-events-none"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>

      <CreateUserModal open={showAdd} onClose={() => setShowAdd(false)} onCreated={fetchUsers} />

      <Modal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Remove Account">
        <div className="space-y-4">
          <p className="text-sm text-gray-400">
            Remove{" "}
            <span className="font-semibold text-white">{deleteTarget?.display_name}</span>? They
            will immediately lose access.
          </p>
          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={() => setDeleteTarget(null)} disabled={deleting}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleDelete} loading={deleting}>
              Remove
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

function MyAccount() {
  const { user, fetchUser } = useAuth();
  const addToast = useUiStore((s) => s.addToast);
  const [displayName, setDisplayName] = useState(user?.display_name ?? "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await usersApi.updateSelf({
        display_name: displayName !== user?.display_name ? displayName : undefined,
        current_password: currentPassword || undefined,
        new_password: newPassword || undefined,
      });
      addToast({ title: "Account updated", variant: "success" });
      setCurrentPassword("");
      setNewPassword("");
      await fetchUser();
    } catch (err) {
      addToast({
        title: "Failed to update account",
        description: err instanceof Error ? err.message : undefined,
        variant: "error",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSave} className="space-y-4">
      <p className="text-sm font-semibold text-gray-300">My Account</p>
      <Input
        label="Display Name"
        value={displayName}
        onChange={(e) => setDisplayName(e.target.value)}
      />
      <div className="grid grid-cols-2 gap-3">
        <Input
          label="Current Password"
          type="password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          placeholder="Required to change password"
        />
        <Input
          label="New Password"
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          hint="At least 8 characters"
        />
      </div>
      <div>
        <Button type="submit" loading={saving}>
          Save Changes
        </Button>
      </div>
    </form>
  );
}

export function AccountsSection() {
  const { user } = useAuth();

  return (
    <div className="space-y-8">
      <MyAccount />
      {user?.role === "owner" && (
        <div className="border-t border-border pt-6">
          <TeamAccounts />
        </div>
      )}
    </div>
  );
}
