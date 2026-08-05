import { useEffect, useState } from "react";
import { Topbar } from "@/components/layout/Topbar";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatCards } from "./StatCards";
import { RecentEvents } from "./RecentEvents";
import { Spinner } from "@/components/ui/Spinner";
import { camerasApi } from "@/api/cameras";
import { eventsApi } from "@/api/events";
import { storageApi } from "@/api/storage";
import type { Camera } from "@/types/camera";
import type { CameraEvent, EventStats } from "@/types/event";

export default function DashboardPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [events, setEvents] = useState<CameraEvent[]>([]);
  const [stats, setStats] = useState<EventStats | null>(null);
  const [recordingsCount, setRecordingsCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [cams, evts, st, storage] = await Promise.all([
          camerasApi.list(),
          eventsApi.list({ page: 1 }),
          eventsApi.stats(),
          storageApi.stats(),
        ]);
        setCameras(cams);
        setEvents(evts);
        setStats(st);
        setRecordingsCount(storage.recordings_count);
      } catch {
        // In dev mode without API, we just show empty state
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const online = cameras.filter((c) => c.status === "online").length;

  return (
    <>
      <Topbar title="Home" />
      <div className="flex-1 overflow-y-auto p-4 lg:p-6">
        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <Spinner size="lg" />
          </div>
        ) : (
          <div className="animate-fade-in space-y-6">
            <StatCards
              camerasOnline={online}
              camerasTotal={cameras.length}
              eventsToday={stats?.total_today ?? 0}
              alertsToday={stats?.alerted_count ?? 0}
              recordingsCount={recordingsCount}
            />
            <PageHeader title="Recent Events" />
            <RecentEvents events={events.slice(0, 6)} />
          </div>
        )}
      </div>
    </>
  );
}