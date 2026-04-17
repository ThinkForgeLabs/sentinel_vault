// pages/Events/index.tsx

import { useEffect, useState, useCallback, useRef } from "react";
import { Topbar } from "@/components/layout/Topbar";
import { PageHeader } from "@/components/layout/PageHeader";
import { Spinner } from "@/components/ui/Spinner";
import { EventFiltersBar } from "./EventFilters";
import { EventList } from "./EventList";
import { EventDetailModal } from "./EventDetailModal";
import { eventsApi } from "@/api/events";
import type { CameraEvent } from "@/types/event";

const POLL_INTERVAL = 15_000;

export default function EventsPage() {
  const [events, setEvents] = useState<CameraEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [selected, setSelected] = useState<CameraEvent | null>(null);

  const initialLoad = useRef(true);

  const fetchEvents = useCallback(async () => {
    if (initialLoad.current) setLoading(true);

    try {
      const type = filter === "all" ? undefined : `${filter}_detected`;
      const data = await eventsApi.list({ event_type: type });
      setEvents(data);
    } catch {
      // silent
    } finally {
      if (initialLoad.current) {
        setLoading(false);
        initialLoad.current = false;
      }
    }
  }, [filter]);

  useEffect(() => {
    initialLoad.current = true;
  }, [filter]);

  useEffect(() => {
    fetchEvents();
    const id = setInterval(fetchEvents, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [fetchEvents]);

  const handleClose = useCallback(() => setSelected(null), []);

  const handleDelete = useCallback(
    async (eventId: string) => {
      try {
        await eventsApi.delete(eventId);

        // Remove from local state immediately (no spinner flicker)
        setEvents((prev) => prev.filter((e) => e.id !== eventId));
        setSelected(null);
      } catch (err) {
        console.error("Delete failed:", err);
      }
    },
    []
  );

  return (
    <>
      <Topbar title="Events" />
      <div className="flex-1 overflow-y-auto p-4 lg:p-6">
        <PageHeader
          title="Events"
          description="AI-detected events from all cameras"
        />
        <div className="mb-5">
          <EventFiltersBar active={filter} onChange={setFilter} />
        </div>
        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <Spinner size="lg" />
          </div>
        ) : (
          <div className="animate-fade-in">
            <EventList events={events} onSelect={setSelected} />
          </div>
        )}
      </div>

      <EventDetailModal
        event={selected}
        onClose={handleClose}
        onDelete={handleDelete}
      />
    </>
  );
}