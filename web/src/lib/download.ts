import { API_URL } from "@/lib/constants";
import { useAuthStore } from "@/store/authStore";

/**
 * Fetch an authenticated file endpoint (recording/clip/export download)
 * and save it to disk. A plain `<a href>` can't carry the Authorization
 * header our API requires, so every download button goes through this:
 * fetch as a blob with the bearer token, then trigger a synthetic anchor
 * click against an object URL.
 */
export async function downloadFile(path: string, fallbackFilename: string): Promise<void> {
  const token = useAuthStore.getState().accessToken;
  const res = await fetch(`${API_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? `Download failed (${res.status})`);
  }

  // Prefer the filename the server chose (Content-Disposition) over our
  // guess, but fall back gracefully if it's ever missing.
  const disposition = res.headers.get("content-disposition") ?? "";
  const match = disposition.match(/filename="?([^";]+)"?/);
  const filename = match?.[1] ?? fallbackFilename;

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
